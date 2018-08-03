# -*- coding: utf-8 -*-
# author: Tiancheng Zhao

from simdial.agent.core import Agent, Action, State, SystemAct, UserAct, BaseSysSlot, BaseUsrSlot
import logging
from collections import OrderedDict
import numpy as np
import copy


class BeliefSlot(object):
    """
    A slot with a probabilistic distribution over the possible values
    槽位在各个曹值上的概率分布

    :ivar value_map: entity_value -> (score, norm_value)
    :ivar last_update_turn: the last turn ID this slot is modified
    :ivar uid: the unique ID, i.e. slot name
    """

    EXPLICIT_THRESHOLD = 0.2            # 需要显式澄清的阈值
    IMPLICIT_THRESHOLD = 0.6            # 需要隐式澄清的阈值
    GROUND_THRESHOLD = 0.95             # 基础阈值

    def __init__(self, uid, vocabulary):
        self.uid = uid
        self.value_map = {}             # 槽位值的map key： slot_val   value: prob
        self.last_update_turn = -1
        self.logger = logging.getLogger(__name__)

    def add_new_observation(self, value, conf, turn_id):
        # 看到曹值，更新最近一次的修改轮数id
        self.last_update_turn = turn_id

        # 更新曹值的置信
        if value in self.value_map.keys():
            # 如果曹值已经出现过，那么在当前置信和之前置信的最大值上加0.2
            prev_conf = self.value_map[value]
            self.value_map[value] = max([prev_conf, conf]) + 0.2
            self.logger.info("Update %s conf to %f at turn %d" % (value, conf, turn_id))
        else:
            # 如果之前没有出现过，那么将其他出现过的曹值的置信都减少一半，
            # 记录当前曹值的置信
            self.value_map = {k: c/2 for k, c in self.value_map.items()}
            self.value_map[value] = conf
            self.logger.info("Add %s conf as %f at turn %d" % (value, conf, turn_id))

    def add_grounding(self, confirm_conf, disconfirm_conf, turn_id, target_value=None):
        '''
        根据confirm_conf, disconfirm_conf两个值更新基础置信度，
        '''
        if len(self.value_map) > 0:
            self.last_update_turn = turn_id
            # 如果target value为空，那么选取当前最大置信的value作为 grounded_value (就是slot最有可能的值)
            if target_value is None:
                grounded_value = self.get_maxconf_value()
            else:
                grounded_value = target_value

            # 更新slot 最有可能的值的 conf
            up_conf = confirm_conf * (1.0 - self.EXPLICIT_THRESHOLD)        # 对曹值的确认概率增益
            down_conf = disconfirm_conf * (1.0 - self.EXPLICIT_THRESHOLD)   # 对曹值的不确定概率增益
            old_conf = self.value_map[grounded_value]
            new_conf = max(0.0, min((old_conf + up_conf - down_conf), 1.5))   # 旧的置信 + 确认增益 - 不确定增益
            self.value_map[grounded_value] = new_conf
            self.logger.info(
                "Ground %s from %f to %f at turn %d" % (grounded_value, old_conf, new_conf, turn_id))
        else:
            self.logger.warn("Warn an concept without value")

    def get_maxconf_value(self):
        '''
        获取置信最大的槽位
        '''
        if len(self.value_map) == 0:
            return None
        max_s, max_v = max([(s, v) for v, s in self.value_map.items()])
        return max_v

    def max_conf(self):
        """
        获取最大的置信度
        :return: the highest confidence of all potential values. 0.0 if its empty
        """
        if len(self.value_map) == 0:
            return 0.0
        return max([s for s in self.value_map.values()])

    def clear(self, turn_id):
        middle = (self.IMPLICIT_THRESHOLD+self.EXPLICIT_THRESHOLD)/2.
        self.value_map = {k: middle for k in self.value_map.keys()}


class BeliefGoal(object):
    '''
    用户目标的状态追踪，这里每个request slot 算作一个goal
    '''
    THRESHOLD = 0.7

    def __init__(self, uid, conf=0.0):
        self.uid = uid
        self.conf = conf
        self.delivered = False        # 是否告诉用户了
        self.value = None             # 当前值
        self.expected_value = None    # 期望值

    def add_observation(self, conf, expected_value):
        # 根据观测更新置信 最大值基础上加0.2，更新期望值的置信概率
        self.conf = max(conf, self.conf) + 0.2
        self.expected_value = expected_value

    def get_conf(self):
        '''
        获取置信
        '''
        return self.conf

    def deliver(self):
        self.delivered = True

    def clear(self):
        self.conf = 0
        self.delivered = False
        self.expected_value = None


class DialogState(State):
    """
    The dialog state class for a system
    dm的状态跟踪类

    :ivar history: the raw dialog history                                            对话历史
    :ivar spk_state: the FSM state for turn-taking. SPK, LISTEN or EXIT              agent的状态
    :ivar valid_entries: a list of valid system entries satisfy the user belief
    :ivar usr_beliefs: a dict of slot name -> BeliefSlot()                           user slot 的置信
    :ivar sys_goals:  a dict of system goal that is obligated to answer              需要回答的sys goal列表
    """
    INFORM_THRESHOLD = 5

    def __init__(self, domain):
        super(State, self).__init__()
        self.history = []
        self.spk_state = self.SPEAK
        self.usr_beliefs = OrderedDict([(s.name, BeliefSlot(s.name, s.vocabulary)) for s in domain.usr_slots])
        self.sys_goals = OrderedDict([(s.name, BeliefGoal(s.name)) for s in domain.sys_slots])
        self.sys_goals[BaseSysSlot.DEFAULT] = BeliefGoal(BaseSysSlot.DEFAULT, conf=1.0)
        self.valid_entries = domain.db.select(self.gen_query())
        self.pending_return = None
        self.domain = domain

    def turn_id(self):
        return len(self.history)

    def gen_query(self):
        """
        :return: a DB compatible query given the current usr beliefs
        获取用户slot的最大置信的value，来组成数据库查询语句
        """
        query = []
        for s in self.usr_beliefs.values():
            max_val = s.get_maxconf_value()
            query.append(max_val)
        return query

    def has_pending_return(self):
        '''
        是否将用户的约束附加到return上
        '''
        return self.pending_return is not None

    def ready_to_inform(self):
        '''
        判断当前是否可以输出信息了
        '''
        # if len(self.valid_entries) <= self.INFORM_THRESHOLD:
        #    return True

        for slot in self.usr_beliefs.values():
            if slot.max_conf() < slot.GROUND_THRESHOLD:
                return False

        for goal in self.sys_goals.values():
            if BeliefGoal.THRESHOLD > goal.get_conf() > 0:
                return False

        return True

    def yield_floor(self, actions):
        if type(actions) is list:
            last_action = actions[-1]
        else:
            last_action = actions
        return last_action.act in [SystemAct.REQUEST, SystemAct.EXPLICIT_CONFIRM, SystemAct.QUERY]

    def is_terminal(self):
        return self.spk_state == State.EXIT

    def reset_sys_goals(self):
        '''
        清空goals
        '''
        for goal in self.sys_goals.values():
            goal.clear()
        self.sys_goals[BaseSysSlot.DEFAULT] = BeliefGoal(BaseSysSlot.DEFAULT, conf=1.0)

    def reset_slots(self):
        for slot in self.usr_beliefs.values():
            slot.clear(self.turn_id)

    def state_summary(self):
        # return a dump of the dialog state
        usr_slots = []
        for slot in self.usr_beliefs.values():
            max_conf = slot.max_conf()
            max_val = slot.get_maxconf_value()
            if max_val is not None:
                usr_slot = self.domain.get_usr_slot(slot.uid)
                max_val = usr_slot.vocabulary[max_val]
            usr_slots.append({'name':slot.uid, 'max_conf': max_conf, 'max_val': max_val})

        sys_goals = []
        for goal in self.sys_goals.values():
            value = goal.value
            exp_value = goal.expected_value
            if value is not None:
                sys_goal = self.domain.get_sys_slot(goal.uid)
                value = sys_goal.vocabulary[value]

            if exp_value is not None:
                sys_goal = self.domain.get_sys_slot(goal.uid)
                exp_value = sys_goal.vocabulary[exp_value]

            sys_goals.append({'name': goal.uid, 'delivered': goal.delivered,
                              'value': value, 'expected': exp_value,
                              'conf': goal.conf})

        return {'usr_slots': usr_slots, 'sys_goals': sys_goals,
                'kb_update': self.has_pending_return()}


class System(Agent):
    """
    basic system agent
    """
    logger = logging.getLogger(__name__)

    def __init__(self, domain, complexity):
        super(System, self).__init__(domain, complexity)
        self.state = DialogState(domain)

    def state_update(self, usr_actions, conf):
        """
        Update the dialog state given system's action in a new turn
        根据最新一轮的用户动作更新DM的状态

        :param usr_actions: a list of system action, None if no action
        :param conf: float [0, 1] confidence of the parsing
        """
        if usr_actions is None or len(usr_actions) == 0:
            return

        self.state.update_history(self.state.USR, usr_actions)      # 更新历史信息
        self.state.spk_state = DialogState.SPEAK                    # 更新对话状态

        # 遍历用户动作列表
        for action in usr_actions:
            # check for user confirm/disconfirm
            # 当前用户的动作是 CONFIRM ，那么更新 user slot 的最可能的value的置信
            if action.act == UserAct.CONFIRM:
                slot, _ = action.parameters[0]
                self.state.usr_beliefs[slot].add_grounding(conf, 1.0 - conf, self.state.turn_id())
            # 当前用户的动作是 DISCONFIRM ，那么更新 user slot 的最可能的value的置信，概率跟上面的情况相反
            elif action.act == UserAct.DISCONFIRM:
                slot, _ = action.parameters[0]
                self.state.usr_beliefs[slot].add_grounding(1.0 - conf, conf, self.state.turn_id())
            # 当前用户的动作是 INFROM ，那么将新的值和conf添加到状态追踪上
            elif action.act == UserAct.INFORM:
                slot, value = action.parameters[0]
                self.state.usr_beliefs[slot].add_new_observation(value, conf, self.state.turn_id())
            # 当前用户的动作是REQUEST 那么 这个slot是系统槽位，更新要返回的goal的置信
            elif action.act == UserAct.REQUEST:
                slot, _ = action.parameters[0]
                self.state.sys_goals[slot].add_observation(conf, None)
            # 当前用户的动作是新的搜索，那么重置sys goal和usr slot 的追踪
            elif action.act == UserAct.NEW_SEARCH:
                self.state.reset_sys_goals()
                self.state.reset_slots()

            # 当前用户的动作是 yes or no 问题
            elif action.act == UserAct.YN_QUESTION:
                # 获取用户认为的 goal slot 的值
                slot, value = action.parameters[0]
                # 更新goals的置信
                self.state.sys_goals[slot].add_observation(conf, value)
            # 如果当前用户满意sys goal slot的值，那么标注sys goal 是已经发出，被用户接受了的
            elif action.act == UserAct.SATISFY or action.act == UserAct.MORE_REQUEST:
                for para, _ in action.parameters:
                    self.state.sys_goals[para].deliver()

            # 如果用户的动作是 kb return , 那么根据query携带的曹值更新sys goal的值
            elif action.act == UserAct.KB_RETURN:
                query = action.parameters[0]
                results = action.parameters[1]
                self.state.pending_return = query
                for slot_name, goal in self.state.sys_goals.items():
                    if slot_name in results.keys():
                        goal.value = results[slot_name]


    def update_grounding(self, sys_actions):
        # 根据当前系统的动作列表，如果系统动作是 IMPLICIT_CONFIRM 更新belief travker的置信值
        if type(sys_actions) is not list:
            sys_actions = [sys_actions]

        for a in sys_actions:
            if a.act == SystemAct.IMPLICIT_CONFIRM:
                slot, value = a.parameters[0]
                self.state.usr_beliefs[slot].add_grounding(1.0, 0.0, self.state.turn_id())

    def policy(self):
        if self.state.spk_state == State.EXIT:
            return None

        # dialog opener
        # 对话历史长度为0，是系统发出 问候动作
        if len(self.state.history) == 0:
            return [Action(SystemAct.GREET), Action(SystemAct.REQUEST, (BaseUsrSlot.NEED, None))]

        # 获取最近一次的用户动作列表
        last_usr = self.state.last_actions(DialogState.USR)
        if last_usr is None:
            raise ValueError("System should talk first")

        # 如果最近一次用户的动作
        actions = []
        for usr_act in last_usr:
            if usr_act.act == UserAct.GOODBYE:
                self.state.spk_state = State.EXIT
                return Action(SystemAct.GOODBYE)

        if self.state.has_pending_return():
            # 将数据查询的约束slot名值对就是query
            # 将它放在goal slot 名值对 之前返回给用户
            query = self.state.pending_return
            goals = {}
            for goal in self.state.sys_goals.values():
                if goal.delivered is False and goal.conf >= BeliefGoal.THRESHOLD:
                    goals[goal.uid] = (goal.value, goal.expected_value)

            actions.append(Action(SystemAct.INFORM, [dict(query), goals]))
            actions.append(Action(SystemAct.REQUEST, (BaseUsrSlot.HAPPY, None)))
            self.state.pending_return = None

            return actions

        # check if it's ready to inform
        elif self.state.ready_to_inform():
            # 如果当前已经可以告诉用户了那么
            # INFORM + {slot -> usr_constrain} + {goal: goal_value}
            # user constrains
            query = [(key, slot.get_maxconf_value()) for key, slot in self.state.usr_beliefs.items()]
            # system goal
            goals = []
            for goal in self.state.sys_goals.values():
                if goal.delivered is False and goal.conf >= BeliefGoal.THRESHOLD:
                    goals.append(goal.uid)
            if len(goals) == 0:
                raise ValueError("Empty goal. Debug!")
            actions.append(Action(SystemAct.QUERY, [query, goals]))
            return actions
        else:
            implicit_confirms = []
            exp_confirms = []
            requests = []

            # 根据槽位状态跟踪信息对slot进行分组
            for slot in self.state.usr_beliefs.values():
                if slot.max_conf() < slot.EXPLICIT_THRESHOLD:
                    exp_confirms.append(Action(SystemAct.REQUEST, (slot.uid, None)))
                elif slot.max_conf() < slot.IMPLICIT_THRESHOLD:
                    requests.append(Action(SystemAct.EXPLICIT_CONFIRM, (slot.uid, slot.get_maxconf_value())))
                elif slot.max_conf() < slot.GROUND_THRESHOLD:
                    implicit_confirms.append(Action(SystemAct.IMPLICIT_CONFIRM, (slot.uid, slot.get_maxconf_value())))

            for goal in self.state.sys_goals.values():
                if BeliefGoal.THRESHOLD > goal.get_conf() > 0:
                    requests.append(Action(SystemAct.REQUEST, (BaseUsrSlot.NEED, None)))
                    break

            if len(exp_confirms) > 0:
                actions.extend(implicit_confirms + exp_confirms[0:1])
                return actions
            elif len(requests) > 0:
                # 显示澄清
                actions.extend(implicit_confirms + requests[0:1])
                return actions
            else:
                return implicit_confirms

    def step(self, inputs, conf):
        """
        Given a list of inputs from the system, generate a response

        :param inputs: a list of Action
        :param conf: the probability that this user input is correct
        :return: reward, terminal, [Action], state
        """
        turn_actions = []
        # update the dialog state
        self.state_update(inputs, conf)
        state = self.state.state_summary()
        while True:
            action = self.policy()

            if action is not None:
                if type(action) is list:
                    turn_actions.extend(action)
                else:
                    turn_actions.append(action)

                self.update_grounding(action)

            if self.state.is_terminal():
                self.state.update_history(self.state.SYS, turn_actions)
                return 0.0, True, turn_actions, state

            if self.state.yield_floor(turn_actions):
                self.state.update_history(self.state.SYS, turn_actions)
                return 0.0, False, turn_actions, state
