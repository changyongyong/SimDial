# -*- coding: utf-8 -*-
# author: Tiancheng Zhao

import logging
import copy


class Agent(object):
    """
    代理基类 持有domain 和 complexity
    Abstract class for Agent (user or system)
    """

    def __init__(self, domain, complexity):
        self.domain = domain
        self.complexity = complexity

    def step(self, *args, **kwargs):
        """
        接收另一个代理的动作，作出应答返回一个action 列表
        Given the new inputs, generate the next response

        :return: reward, terminal, response
        """
        raise NotImplementedError("Implement step function is required")


class Action(dict):
    """
    A generic class that corresponds to a discourse unit. An action is made of an Act and a list of parameters.
    Action 的基类 描述agent的最小动作单元 持有act 类型 和act 参数列表[(slot_name=slot_val),]
    :ivar act: dialog act String
    :ivar parameters: [{slot -> usr_constrain}, {sys_slot -> value}] for INFORM, and [(type, value)...] for other acts.

    """

    def __init__(self, act, parameters=None):
        self.act = act
        if parameters is None:
            self.parameters = []
        elif type(parameters) is not list:
            self.parameters = [parameters]
        else:
            self.parameters = parameters
        super(Action, self).__init__(act=self.act, parameters=self.parameters)

    def add_parameter(self, type, value):
        self.parameters.append((type, value))

    def dump_string(self):
        str_paras = []
        for p in self.parameters:
            if type(p) is not str:
                str_paras.append(str(p))
            else:
                str_paras.append(p)
        str_paras = "-".join(str_paras)
        return "%s:%s" % (self.act, str_paras)


class State(object):
    """
    The base class for a dialog state
    状态管理器的基类

    :ivar history: a list of turns
    :cvar USR: user name
    :cvar SYS: system name
    :cvar LISTEN: the agent is waiting for other's input
    :cvar SPEAK: the agent is generating it's output
    :cvar EXT: the agent leaves the session
    """

    # 代理角色
    USR = "usr"
    SYS = "sys"

    # 代理状态
    LISTEN = "listen"
    SPEAK = "speak"
    EXIT = "exit"

    def __init__(self):
        self.history = []

    def yield_floor(self, *args, **kwargs):
        """
        Base function that decides if the agent should yield the conversation floor
        基础函数，决定代理是否返回 对话的 floor 动作 ，就是一个结束性动作
        """
        raise NotImplementedError("Yield is required")

    def is_terminal(self, *args, **kwargs):
        """
        Base function decides if the agent is left
        判断当前代理是否结束会话
        """
        raise NotImplementedError("is_terminal is required")

    def last_actions(self, target_speaker):
        """
        Search in the dialog hisotry given a speaker.
        给定代理角色，返回该代理最近一轮的动作

        :param target_speaker: the target speaker
        :return: the last turn produced by the given speaker. None if not found.
        """
        for spk, utt in self.history[::-1]:
            if spk == target_speaker:
                return utt
        return None

    def update_history(self, speaker, actions):
        """
        Append the new turn into the history
        更新对话历史

        :param speaker: SYS or USR
        :param actions: a list of Action
        """
        # make a deep copy of actions
        self.history.append((speaker, copy.deepcopy(actions)))


class SystemAct(object):
    """
    系统动作
    :cvar IMPLICIT_CONFIRM: you said XX      确定性要求用户确认
    :cvar EXPLICIT_CONFIRM: do you mean XX   不确定性要求用户确认
    :cvar INFORM: I think XX is a good fit   提供槽位值信息 goal类型槽位
    :cvar REQUEST: which location?           反问槽位值信息 constrain 类型槽位
    :cvar GREET: hello                       问候打招呼
    :cvar GOODBYE: goodbye                   离开
    :cvar CLARIFY: I think you want either A or B. Which one is right?   澄清
    :cvar ASK_REPHRASE: can you please say it in another way?            换一种方式说
    :cvar ASK_REPEAT: what did you say?                                  再说一遍
    """

    IMPLICIT_CONFIRM = "implicit_confirm"
    EXPLICIT_CONFIRM = "explicit_confirm"
    INFORM = "inform"
    REQUEST = "request"
    GREET = "greet"
    GOODBYE = "goodbye"
    CLARIFY = "clarify"
    ASK_REPHRASE = "ask_rephrase"
    ASK_REPEAT = "ask_repeat"
    QUERY = "query"


class UserAct(object):
    """
    用户角色动作
    :cvar CONFIRM: yes                       确认
    :cvar DISCONFIRM: no                     否认
    :cvar YN_QUESTION: Is it going to rain?  确认否认问题
    :cvar INFORM: I like Chinese food.       提供槽位信息
    :cvar REQUEST: find me a place to eat.   问goal类型槽位
    :cvar GREET: hello                       打招呼
    :cvar NEW_SEARCH: I have a new request.  新的问题
    :cvar GOODBYE: goodbye                   离开
    :cvar CHAT: how is your day              聊天
    """
    GREET = "greet"
    INFORM = "inform"
    REQUEST = "request"
    YN_QUESTION = "yn_question"
    CONFIRM = "confirm"
    DISCONFIRM = "disconfirm"
    GOODBYE = "goodbye"
    NEW_SEARCH = "new_search"
    CHAT = "chat"
    SATISFY = "satisfy"
    MORE_REQUEST = "more_request"
    KB_RETURN = "kb_return"


class BaseSysSlot(object):
    """
    基础系统类型slot
    :cvar DEFAULT: the db entry             数据库 entry
    :cvar PURPOSE: what's the purpose of the system   系统的目的
    """

    PURPOSE = "#purpose"
    DEFAULT = "#default"


class BaseUsrSlot(object):
    """
    基础用户类型slot
    :cvar NEED: what user want                需求槽
    :cvar HAPPY: if user is satisfied about system's results   满意槽
    :cvar AGAIN: the user rephrase the same sentence.          换一种方式槽
    :cvar SELF_CORRECT: the user correct itself.               修改槽
    """
    NEED = "#need"
    HAPPY = "#happy"
    AGAIN = "#again"
    SELF_CORRECT = "#self_correct"
