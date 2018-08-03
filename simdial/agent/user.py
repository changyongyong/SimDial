# -*- coding: utf-8 -*-
# author: Tiancheng Zhao
from simdial.agent.core import Agent, Action, UserAct, SystemAct, BaseSysSlot, BaseUsrSlot, State
import logging
import numpy as np
import copy
from collections import OrderedDict


class User(Agent):
    """
    Basic user agent

    :ivar usr_constrains: a combination of user slots   用户槽位约束
    :ivar domain: the given domain                      领域名
    :ivar state: the dialog state                       对话状态跟踪
    """

    logger = logging.getLogger(__name__)

    class DialogState(State):
        """
        The dialog state object for this user simulator

        :ivar history: a list of tuple [(speaker, actions) ... ]
        :ivar spk_state: LISTEN, SPEAK or EXIT
        :ivar goals_met: if the system propose anything that's in user's goal
        :ivar: input_buffer: a list of system action that is not being handled in this turn
        """
        def __init__(self, sys_goals):
            super(State, self).__init__()
            self.history = []
            self.spk_state = self.LISTEN
            self.input_buffer = []
            self.goals_met = OrderedDict([(g, False) for g in sys_goals])

        def update_history(self, speaker, actions):
            """
            :param speaker: SYS or USR
            :param actions: a list of Action
            """
            self.history.append((speaker, actions))

        def is_terminal(self):
            """
            :return: the user wants to terminate the session
            """
            return self.spk_state == self.EXIT

        def yield_floor(self):
            """
            :return: True if user want to stop speaking
            """
            return self.spk_state == self.LISTEN

        def unmet_goal(self):
            '''
            获取没有完成的目的槽位
            '''
            for k, v in self.goals_met.items():
                if v is False:
                    return k
            return None

        def update_goals_met(self, top_action):
            '''
            更新 目的槽的完成状态
            '''
            proposed_sys = top_action.parameters[1]
            completed_goals = []
            for goal in proposed_sys.keys():
                if goal in self.goals_met.keys():
                    self.goals_met[goal] = True
                    completed_goals.append(goal)
            return completed_goals

        def reset_goal(self, sys_goals):
            self.goals_met = {g: False for g in sys_goals}

    def __init__(self, domain, complexity):
        super(User, self).__init__(domain, complexity)
        # 随机的选择目的槽位的个数
        self.goal_cnt = np.random.choice(complexity.multi_goals.keys(), p=complexity.multi_goals.values())
        self.goal_ptr = 0           # 目的槽的指针
        self.usr_constrains, self.sys_goals = self._sample_goal()       # 采样目标和用户约束
        self.state = self.DialogState(self.sys_goals)                   # 使用系统目的槽列表初始化对话状态

    def state_update(self, sys_actions):
        """
        Update the dialog state given system's action in a new turn

        :param sys_actions: a list of system action
        """
        self.state.update_history(self.state.SYS, sys_actions)    # 更新对话历史
        self.state.spk_state = self.DialogState.SPEAK             # 当前状态为正在进行
        self.state.input_buffer = copy.deepcopy(sys_actions)      # 将系统动作列表作为输入缓存

    def _sample_goal(self):
        """
        :return: {slot_name -> value} for user constrains, [slot_name, ..] for system goals
        """
        temp_constrains = self.domain.db.sample_unique_row().tolist()     # 从数据库中采样一个用户约束
        # 根据复杂阈值随机的指定某些槽位时可以忽略的(值为none)
        temp_constrains = [None if np.random.rand() < self.complexity.dont_care
                           else c for c in temp_constrains]
        # 将采样到的约束值复制给当前领域的usr_slots
        usr_constrains = {s.name: temp_constrains[i] for i, s in enumerate(self.domain.usr_slots)}

        # 随机的选取 goal slot的个数
        num_interest = np.random.randint(0, len(self.domain.sys_slots)-1)
        goal_candidates = [s.name for s in self.domain.sys_slots if s.name != BaseSysSlot.DEFAULT]
        # 选出这些goal
        selected_goals = np.random.choice(goal_candidates, size=num_interest, replace=False)
        np.random.shuffle(selected_goals)
        sys_goals = [BaseSysSlot.DEFAULT] + selected_goals.tolist()
        return usr_constrains, sys_goals

    def _constrain_equal(self, top_action):
        # 判断 系统追踪的约束是否和user设定的一致
        proposed_constrains = top_action.parameters[0]
        for k, v in self.usr_constrains.items():
            if k in proposed_constrains:
                if v != proposed_constrains[k]:
                    return False, k
            else:
                return False, k
        return True, None

    def _increment_goal(self):
        '''
        跟新goal的指针，并随机的跟新约束槽位的值
        '''
        if self.goal_ptr >= self.goal_cnt-1:
            return None
        else:
            self.goal_ptr += 1
            _, self.sys_goals = self._sample_goal()
            change_key = np.random.choice(self.usr_constrains.keys())
            change_slot = self.domain.get_usr_slot(change_key)
            old_value = self.usr_constrains[change_key]
            old_value = -1 if old_value is None else old_value
            new_value = np.random.randint(0, change_slot.dim-1) % change_slot.dim
            self.logger.info("Filp user constrain %s from %d to %d" %
                             (change_key, old_value, new_value))
            self.usr_constrains[change_key] = new_value
            self.state.reset_goal(self.sys_goals)
            return change_key

    def policy(self):
        if self.state.spk_state == self.DialogState.EXIT:
            return None

        if len(self.state.input_buffer) == 0:
            self.state.spk_state = self.DialogState.LISTEN
            return None

        if len(self.state.history) > 100:
            self.state.input_buffer = []
            return Action(UserAct.GOODBYE)

        # 取出缓存的第一system act
        top_action = self.state.input_buffer[0]
        self.state.input_buffer.pop(0)

        if top_action.act == SystemAct.GREET:
            return Action(UserAct.GREET)

        elif top_action.act == SystemAct.GOODBYE:
            return Action(UserAct.GOODBYE)

        # 系统是确定性澄清
        elif top_action.act == SystemAct.IMPLICIT_CONFIRM:
            if len(top_action.parameters) == 0:
                raise ValueError("IMPLICIT_CONFIRM is required to have parameter")
            # 取出第一对 需要澄清的 slot name 和slot value
            slot_type, slot_val = top_action.parameters[0]

            # 判断当前slot 是否是用户slot
            if self.domain.is_usr_slot(slot_type):
                # if the confirm is right or usr does not care about this slot
                # 如果需要澄清的slot满足约束或约束值为None name返回None
                if slot_val == self.usr_constrains[slot_type] or self.usr_constrains[slot_type] is None:
                    return None
                else:
                    # 不满足,则选择 否认曹值动作 或是 否认曹值动作 + 提供正确的曹值
                    strategy = np.random.choice(self.complexity.reject_style.keys(),
                                                p=self.complexity.reject_style.values())
                    if strategy == "reject":
                        return Action(UserAct.DISCONFIRM, (slot_type, slot_val))
                    elif strategy == "reject+inform":
                        return [Action(UserAct.DISCONFIRM, (slot_type, slot_val)),
                                Action(UserAct.INFORM, (slot_type, self.usr_constrains[slot_type]))]
                    else:
                        raise ValueError("Unknown reject strategy")
            else:
                raise ValueError("Usr cannot handle imp_confirm to non-usr slots")

        # 如果是非确定性澄清
        elif top_action.act == SystemAct.EXPLICIT_CONFIRM:
            if len(top_action.parameters) == 0:
                raise ValueError("EXPLICIT_CONFIRM is required to have parameter")
            slot_type, slot_val = top_action.parameters[0]
            if self.domain.is_usr_slot(slot_type):
                # if the confirm is right or usr does not care about this slot
                # 满足约束，则返回确认动作
                if slot_val == self.usr_constrains[slot_type]:
                    return Action(UserAct.CONFIRM, (slot_type, slot_val))
                else:
                    return Action(UserAct.DISCONFIRM, (slot_type, slot_val))
            else:
                raise ValueError("Usr cannot handle imp_confirm to non-usr slots")

        # 系统动作是 INFROM
        elif top_action.act == SystemAct.INFORM:
            if len(top_action.parameters) != 2:
                raise ValueError("INFORM needs to contain the constrains and goal (2 parameters)")

            # 验证系统状态追踪是否满足约束
            valid_constrain, wrong_slot = self._constrain_equal(top_action)
            if valid_constrain:
                # 满足约束，就跟新goal的状态，随机选择下一个goal
                complete_goals = self.state.update_goals_met(top_action)
                next_goal = self.state.unmet_goal()

                # 下一个goal为None
                if next_goal is None:
                    # 下一个goal为空，随机更新约束条件
                    slot_key = self._increment_goal()
                    if slot_key is not None:
                        # 要跟新的约束不为空，则新搜索动作，并告诉系统更新的约束
                        return [Action(UserAct.NEW_SEARCH, (BaseSysSlot.DEFAULT, None)),
                                Action(UserAct.INFORM, (slot_key, self.usr_constrains[slot_key]))]
                    else:
                        # 否则 告诉系统满意搜索结果，返回离开动作
                        return [Action(UserAct.SATISFY, [(g, None) for g in complete_goals]),
                                Action(UserAct.GOODBYE)]
                else:
                    #下一个goal不为空
                    ack_act = Action(UserAct.MORE_REQUEST, [(g, None) for g in complete_goals])
                    # 随机的返回是否是yes or no问题 ，就是用户提供一个goal值，问系统是不是
                    if np.random.rand() < self.complexity.yn_question:
                        # find a system slot with yn_templates
                        slot = self.domain.get_sys_slot(next_goal)
                        expected_val = np.random.randint(0, slot.dim)
                        if len(slot.yn_questions.get(slot.vocabulary[expected_val], [])) > 0:
                            # sample a expected value
                            return [ack_act, Action(UserAct.YN_QUESTION, (slot.name, expected_val))]

                    # 否则正常的问系统
                    return [ack_act, Action(UserAct.REQUEST, (next_goal, None))]
            else:
                # 如果不满足约束条件，那么告诉系统正确的约束条件
                return Action(UserAct.INFORM, (wrong_slot, self.usr_constrains[wrong_slot]))

        # 如果系统的动作是 request
        elif top_action.act == SystemAct.REQUEST:
            if len(top_action.parameters) == 0:
                raise ValueError("Request is required to have parameter")

            slot_type, slot_val = top_action.parameters[0]

            # 系统问的是你还有什么需求
            if slot_type == BaseUsrSlot.NEED:
                # 返回一个没有满足的goal
                next_goal = self.state.unmet_goal()
                return Action(UserAct.REQUEST, (next_goal, None))

            # 系统返回的槽位时happy，那么什么都不做
            elif slot_type == BaseUsrSlot.HAPPY:
                return None

            # 如果是系统约束槽位
            elif self.domain.is_usr_slot(slot_type):
                # 采样出随机个数的多余槽位，将动作排在当前槽位之后inform
                if len(self.domain.usr_slots) > 1:
                    num_informs = np.random.choice(self.complexity.multi_slots.keys(),
                                                   p=self.complexity.multi_slots.values(),
                                                   replace=False)
                    if num_informs > 1:
                        candidates = [k for k, v in self.usr_constrains.items() if k != slot_type and v is not None]
                        num_extra = min(num_informs-1, len(candidates))
                        if num_extra > 0:
                            extra_keys = np.random.choice(candidates, size=num_extra, replace=False)
                            actions = [Action(UserAct.INFORM, (key, self.usr_constrains[key])) for key in extra_keys]
                            actions.insert(0, Action(UserAct.INFORM, (slot_type, self.usr_constrains[slot_type])))
                            return actions

                return Action(UserAct.INFORM, (slot_type, self.usr_constrains[slot_type]))

            else:
                raise ValueError("Usr cannot handle request to this type of parameters")

        # 没有处理澄清
        elif top_action.act == SystemAct.CLARIFY:
            raise ValueError("Cannot handle clarify now")

        # 再说一遍，就将历史turn取出输出
        elif top_action.act == SystemAct.ASK_REPEAT:
            last_usr_actions = self.state.last_actions(self.state.USR)
            if last_usr_actions is None:
                raise ValueError("Unexpected ask repeat")
            return last_usr_actions

        # 换一种方式说
        elif top_action.act == SystemAct.ASK_REPHRASE:
            # 取出最近一轮，并将action的参数中追加again标志
            last_usr_actions = self.state.last_actions(self.state.USR)

            if last_usr_actions is None:
                raise ValueError("Unexpected ask rephrase")
            for a in last_usr_actions:
                a.add_parameter(BaseUsrSlot.AGAIN, True)
            return last_usr_actions

        # 如果系统是query 问满足约束的goal值是不是你要的，
        # 就从数据库中采样出goals的值，并告诉系统
        elif top_action.act == SystemAct.QUERY:
            query, goals = top_action.parameters[0], top_action.parameters[1]
            valid_entries = self.domain.db.select([v for name, v in query])
            chosen_entry = valid_entries[np.random.randint(0, len(valid_entries)), :]

            results = {}
            if chosen_entry.shape[0] > 0:
                for goal in goals:
                    _, slot_id = self.domain.get_sys_slot(goal, return_idx=True)
                    results[goal] = chosen_entry[slot_id]
            else:
                print(chosen_entry)
                raise ValueError("No valid entries")

            return Action(UserAct.KB_RETURN, [query, results])
        else:
            raise ValueError("Unknown system act %s" % top_action.act)

    def step(self, inputs):
        """
        Given a list of inputs from the system, generate a response

        :param inputs: a list of Action
        :return: reward, terminal, [Action]
        """
        turn_actions = []
        # update the dialog state
        self.state_update(inputs)
        while True:
            action = self.policy()
            if action is not None:
                if type(action) is list:
                    turn_actions.extend(action)
                else:
                    turn_actions.append(action)

            if self.state.is_terminal():
                reward = 1.0 if self.state.unmet_goal() is None else -1.0
                self.state.update_history(self.state.USR, turn_actions)
                return reward, True, turn_actions

            if self.state.yield_floor():
                self.state.update_history(self.state.USR, turn_actions)
                return 0.0, False, turn_actions
