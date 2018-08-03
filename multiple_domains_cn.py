# -*- coding: utf-8 -*-
# author: Tiancheng Zhao
from simdial.domain import Domain, DomainSpec
from simdial.generator import Generator
from simdial import complexity
import string

'''
中文多领域定义
'''

class RestSpec(DomainSpec):
    name = "restaurant"
    greet = "欢迎访问酒店推荐系统."
    nlg_spec = {"loc": {"inform": ["我现在在  %s.", "%s.", "我对 %s的食物比较感兴趣.", "在 %s.", "在 %s 里."],
                        "request": ["你对那个城市比较感兴趣?", "什么地方?"]},

                "food_pref": {"inform": ["我喜欢 %s 的食物.", "%s 的食物.", "%s 的酒店.", "%s."],
                              "request": ["你喜欢什么类型的食物?", "你喜欢什么类型的酒店?"]},

                "open": {"inform": ["那个酒店现在 %s.", "现在 %s 了."],
                         "request": ["哪个酒店营业时间是什么.", "什么时候营业么?"],
                         "yn_question": {'开门': ["现在营业么?"],
                                         '关门': ["现在停止营业了么?"]
                                         }},

                "parking": {"inform": ["酒店有 %s.", "这个地方有 %s."],
                            "request": ["它由什么类型的停车位?.", "它方便停车么?"],
                            "yn_question": {'路边停车位': ["它由路边停车位么?"],
                                            "专门停车位": ["它有专门的停车位么?"]
                                            }},

                "price": {"inform": ["酒店提供 %s 食物.", "价格是 %s."],
                          "request": ["那里的平均价格是?", "那里的价位是多少?"],
                          "yn_question": {'昂贵': ["酒店消费很昂贵么?"],
                                          '平价': ["酒店提供平价的服务么?"],
                                          '便宜': ["酒店消费便宜么?"]
                                          }},

                "default": {"inform": [" %s 酒店是一个不错的选择."],
                            "request": ["我需要订一个酒店.",
                                        "我想找一家酒店.",
                                        "推荐一个吃饭的地方."]}
                }

    usr_slots = [("loc", "location city", ["北京", "上海", "天津", "大连",
                                           "西安", "杭州", "厦门",
                                           "成都", "桂林", "海南"]),
                 ("food_pref", "food preference", ["泰国", "鲁", "粤", "日本",
                                                   "韩国", "法国", "印度", "意大利",
                                                   "川", "台湾", "美国"])]

    sys_slots = [("open", "if it's open now", ["开门", "关门"]),
                 ("price", "average price per person", ["便宜", "平价", "昂贵"]),
                 ("parking", "if it has parking", ["路边停车位", "专用停车位", "没有停车位"])]

    db_size = 100


class RestStyleSpec(DomainSpec):
    name = "restaurant_style"
    greet = "你好，我想找一家用餐的地方"
    nlg_spec = {"loc": {"inform": ["我现在在 %s.", "%s.", "我对 %s 的食物感兴趣.", "在 %s.", "在 %s."],
                        "request": ["你现在在什么地方?", "好的，你的位置是?"]},

                "food_pref": {"inform": ["我喜欢 %s 的食品.", "%s 的食品.", "%s 的饭店.", "%s."],
                              "request": ["你喜欢什么烹饪方式", "你想吃什么?"]},

                "open": {"inform": ["一个不错的选择是 %s.", "目前合适的选择是 %s."],
                         "request": ["告诉我那个酒店营业时间是.", "它营业的时间是?"],
                         "yn_question": {'开门': ["现在酒店营业么?"],
                                         '关门': ["现在关门了么?"]
                                         }},

                "parking": {"inform": ["停车位是 %s.", "它提供停车服务是 %s."],
                            "request": ["它提供什么停车服务?.", "方便听成么?"],
                            "yn_question": {'路边停车位': ["它有路边停车位么?"],
                                            "专用停车位": ["它有专用停车位么?"]
                                            }},

                "price": {"inform": ["那里提供 %s 的食物.", "我查一下. 那里的价位是 %s."],
                          "request": ["那里的平均价位是?", "那里贵么?"],
                          "yn_question": {'昂贵': ["那里消费昂贵么?"],
                                          '平价': ["它是平价的么?"],
                                          '便宜': ["它便宜么?"]
                                          }},

                "default": {"inform": ["我查看一下数据库, %s 是一个不错的选择."],
                            "request": ["我想订一家酒店.",
                                        "我在找一家酒店.",
                                        "推荐一个吃饭的地方吧."]}
                }

    usr_slots = [("loc", "location city", ["上海", "北京", "西安", "青岛",
                                           "大连", "石家庄", "天津",
                                           "桂林", "成都", "深圳"]),
                 ("food_pref", "food preference", ["泰国", "鲁", "韩国", "日本",
                                                   "美国", "印度", "粤", "法国",
                                                   "川", "墨西哥", "台湾", "意大利"])]

    sys_slots = [("open", "if it's open now", ["开门", "关门"]),
                 ("price", "average price per person", ["便宜", "平价", "昂贵"]),
                 ("parking", "if it has parking", ["路边停车位", "专用停车位", "无停车位"])]

    db_size = 100


class RestPittSpec(DomainSpec):
    name = "rest_pitt"
    greet = "I am an expert about Pittsburgh restaurant."

    nlg_spec = {"loc": {"inform": ["I am at %s.", "%s.", "I'm interested in food at %s.", "At %s.", "In %s."],
                        "request": ["Which city are you interested in?", "Which place?"]},

                "food_pref": {"inform": ["I like %s food.", "%s food.", "%s restaurant.", "%s."],
                              "request": ["What kind of food do you like?", "What type of restaurant?"]},

                "open": {"inform": ["The restaurant is %s.", "It is %s right now."],
                         "request": ["Tell me if the restaurant is open.", "What's the hours?"],
                         "yn_question": {'open': ["Is the restaurant open?"],
                                         'closed': ["Is it closed?"]
                                         }},

                "parking": {"inform": ["The restaurant has %s.", "This place has %s."],
                            "request": ["What kind of parking does it have?.", "How easy is it to park?"],
                            "yn_question": {'street parking': ["Does it have street parking?"],
                                            "valet parking": ["Does it have valet parking?"]
                                            }},

                "price": {"inform": ["The restaurant serves %s food.", "The price is %s."],
                          "request": ["What's the average price?", "How expensive it is?"],
                          "yn_question": {'expensive': ["Is it expensive?"],
                                          'moderate': ["Does it have moderate price?"],
                                          'cheap': ["Is it cheap?"]
                                          }},

                "default": {"inform": ["Restaurant %s is a good choice."],
                            "request": ["I need a restaurant.",
                                        "I am looking for a restaurant.",
                                        "Recommend me a place to eat."]}
                }

    usr_slots = [("loc", "location city", ["Downtown", "CMU", "Forbes and Murray", "Craig",
                                           "Waterfront", "Airport", "U Pitt", "Mellon Park",
                                           "Lawrance", "Monroveil", "Shadyside", "Squrill Hill"]),
                 ("food_pref", "food preference", ["healthy", "fried", "panned", "steamed", "hot pot",
                                                   "grilled", "salad", "boiled", "raw", "stewed"])]

    sys_slots = [("open", "if it's open now", ["open", "going to start", "going to close", "closed"]),
                 ("price", "average price per person", ["cheap", "average", "fancy"]),
                 ("parking", "if it has parking", ["garage parking", "street parking", "no parking"])]

    db_size = 150


class BusSpec(DomainSpec):
    name = "bus"
    greet = "你可以问我公交车的信息."

    nlg_spec = {"from_loc": {"inform": ["我现在在 %s.", "%s.", "出发地是 %s.", "在 %s.", "从 %s 出发."],
                             "request": ["你从哪里出发?", "你的出发地是哪里?"]},

                "to_loc": {"inform": ["去 %s.", "%s.", "目的地是 %s.", "打算去 %s.", "到 %s"],
                           "request": ["你要去哪里?", "你的目的地是哪里?"]},

                "datetime": {"inform": ["在 %s.", "%s.", "我 %s 出发.", "出发时间是 %s."],
                             "request": ["你什么时候出发?", "你需要什么时间段的公交车?"]},

                "arrive_in": {"inform": ["那个公交车在 %s 分内到达.", "等车用时 %s 分钟.",
                                         "在 %s 分内到达"],
                              "request": ["多长时间到达?", "我需要等待多长时间?",
                                          "估计需要多长时间"],
                              "yn_question": {k: ["会等的很长么?"] if k>15 else ["等待时间短么?"]
                                              for k in range(0, 30, 5)}},

                "duration": {"inform": ["路程耗时 %s 分.", "旅程时间是 %s 分钟."],
                             "request": ["路上用时多长?.", "用多长时间到达目的地?"],
                              "yn_question": {k: ["路程耗时长么?"] if k>30 else ["路程耗时短么?"]
                                              for k in range(0, 60, 5)}},

                "default": {"inform": ["%s 公交车可以带你去那里."],
                            "request": ["我要查询公交信息.",
                                        "我要找一辆公交车.",
                                        "推荐一辆公交车吧."]}
                }

    usr_slots = [("from_loc", "departure place", ["北土城", "北大", "六里桥", "海淀黄庄",
                                                  "苏州街", "西二旗", "望京", "北京南站",
                                                  "磁器口", "西单", "国贸", "王府井"]),
                 ("to_loc", "arrival place", ["北土城", "北大", "六里桥", "海淀黄庄",
                                              "苏州街", "西二旗", "望京", "北京南站",
                                              "磁器口", "西单", "国贸", "王府井"]),
                 ("datetime", "leaving time", ["今天", "明天", "今晚", "今天早晨",
                                               "今天中午"] + [str(t+1) for t in range(24)])
                 ]

    sys_slots = [("arrive_in", "how soon it arrives", [str(t) for t in range(0, 30, 5)]),
                 ("duration", "how long it takes", [str(t) for t in range(0, 60, 5)])
                 ]

    db_size = 150


class WeatherSpec(DomainSpec):
    name = "weather"
    greet = "你可以问我天气信息."

    nlg_spec = {"loc": {"inform": ["我现在在 %s.", "%s.", "%s 的天气.", "%s 的.", "是 %s."],
                        "request": ["你想知道那个城市的?", "哪里的?"]},

                "datetime": {"inform": ["日期是 %s", "%s.", "我想知道 %s 的."],
                             "request": ["你想知道哪天的?", "日期是?"]},

                "temperature": {"inform": ["气温是 %s.", "那时的气温是 %s."],
                                "request": ["气温是?", "气温是多少?"]},

                "weather_type": {"inform": ["天气是 %s.", "天气会是 %s."],
                                 "request": ["天气怎样?.", "天气如何"],
                                 "yn_question": {k: ["天气是 %s 么?" % k] for k in
                                                 ["下雨", "下雪", "刮风", "晴朗", "雾霾", "多云"]}
                                 },

                "default": {"inform": ["你的天气预报 %s 在这里."],
                            "request": ["天气怎么样?.",
                                        "天气将会是?"]}
                }

    usr_slots = [("loc", "location city", ["北京", "上海", "广州", "深圳",
                                           "厦门", "南京", "杭州",
                                           "徐州", "大连", "青岛"]),
                 ("datetime", "which time's weather?", ["今天", "明天", "今晚", "今晨",
                                                        "后天", "周末"])]

    sys_slots = [("temperature", "the temperature", [str(t) for t in range(20, 40, 2)]),
                 ("weather_type", "the type", ["下雨", "下雪", "刮风", "晴朗", "雾霾", "多云"])]

    db_size = 40


class MovieSpec(DomainSpec):
    name = "movie"
    greet = "你想咨询电影信息么?"

    nlg_spec = {"genre": {"inform": ["我喜欢 %s 的电影.", "%s.", "我喜欢 %s 的.", "%s 类型的电影."],
                          "request": ["你喜欢什么类型的?", "那种类型的电影?"]},

                "years": {"inform": [" %s 年的电影", " %s 年的."],
                          "request": ["你喜欢什么年代的?", "什么年代的电影?"]},

                "country": {"inform": ["%s的电影", "%s.", "%s的."],
                            "request": ["哪个国家的?", "电影是哪个国家的?"]},

                "rating": {"inform": ["电影的评分是 %s.", "评分是 %s."],
                           "request": ["评分是多少?", "人们对这个电影的评分是多少?"],
                           "yn_question": {"5": ["它的评分高么?"],
                                           "4": ["它的评分是 4/5 么?"],
                                           "1": ["它的评分很低么?"]}
                           },

                "company": {"inform": ["它的制片公司是 %s.", "它是由 %s 出品的."],
                            "request": ["它的出品公司是哪个?.", "哪个出品公司的?"],
                            "yn_question": {k: ["它的出品公司是 %s 么?" % k] for k in
                                            ["20世纪福克斯", "索尼", "MGM", "迪士尼", "环球影业"]}
                            },

                "director": {"inform": ["它的导演是 %s.", "它是由 %s 执导的."],
                             "request": ["它的导演是?.", "谁导演的它?"],
                             "yn_question": {k: ["它的导演是 %s 么?" % k] for k in
                                             list(string.ascii_uppercase)}
                             },

                "default": {"inform": ["电影 %s 是一个不错的选择."],
                            "request": ["推荐一个电影.",
                                        "给我一些观影建议吧.",
                                        "我现在可以看什么呀"]}
                }

    usr_slots = [("genre", "type of movie", ["动作", "科幻", "喜剧", "犯罪",
                                             "体育", "记录片", "舞台剧",
                                             "家庭", "恐怖", "战争", "音乐", "奇幻", "浪漫", "西部"]),

                 ("years", "when", ["60s", "70s", "80s", "90s", "2000-2010", "2010-present"]),

                 ("country", "where ", ["美国", "法国", "中国", "韩国",
                                        "日本", "德国", "墨西哥", "俄国", "台湾"])
                 ]

    sys_slots = [("rating", "user rating", [str(t) for t in range(5)]),
                 ("company", "the production company", ["20世纪福克斯", "索尼", "MGM", "迪士尼", "环球影业"]),
                 ("director", "the director's name", list(string.ascii_uppercase))
                 ]

    db_size = 200


if __name__ == "__main__":
    # pipeline here
    # generate a fix 500 test set and 5000 training set.
    # generate them separately so the model can choose a subset for train and
    # test on all the test set to see generalization.

    test_size = 5
    train_size = 20
    gen_bot = Generator()

    rest_spec = RestSpec()
    rest_style_spec = RestStyleSpec()
    #rest_pitt_spec = RestPittSpec()
    bus_spec = BusSpec()
    movie_spec = MovieSpec()
    weather_spec = WeatherSpec()

    # restaurant
    gen_bot.gen_corpus("test", rest_spec, complexity.CleanSpec, test_size)
    gen_bot.gen_corpus("test", rest_spec, complexity.MixSpec, test_size)
    gen_bot.gen_corpus("train", rest_spec, complexity.CleanSpec, train_size)
    gen_bot.gen_corpus("train", rest_spec, complexity.MixSpec, train_size)

    # restaurant style
    gen_bot.gen_corpus("test", rest_style_spec, complexity.CleanSpec, test_size)
    gen_bot.gen_corpus("test", rest_style_spec, complexity.MixSpec, test_size)
    gen_bot.gen_corpus("train", rest_style_spec, complexity.CleanSpec, train_size)
    gen_bot.gen_corpus("train", rest_style_spec, complexity.MixSpec, train_size)

    # bus
    gen_bot.gen_corpus("test", bus_spec, complexity.CleanSpec, test_size)
    gen_bot.gen_corpus("test", bus_spec, complexity.MixSpec, test_size)
    gen_bot.gen_corpus("train", bus_spec, complexity.CleanSpec, train_size)
    gen_bot.gen_corpus("train", bus_spec, complexity.MixSpec, train_size)

    # weather
    gen_bot.gen_corpus("test", weather_spec, complexity.CleanSpec, test_size)
    gen_bot.gen_corpus("test", weather_spec, complexity.MixSpec, test_size)
    gen_bot.gen_corpus("train", weather_spec, complexity.CleanSpec, train_size)
    gen_bot.gen_corpus("train", weather_spec, complexity.MixSpec, train_size)

    # movie
    gen_bot.gen_corpus("test", movie_spec, complexity.CleanSpec, test_size)
    gen_bot.gen_corpus("test", movie_spec, complexity.MixSpec, test_size)
    gen_bot.gen_corpus("train", movie_spec, complexity.CleanSpec, train_size)
    gen_bot.gen_corpus("train", movie_spec, complexity.MixSpec, train_size)

    # restaurant Pitt
    #gen_bot.gen_corpus("test", rest_pitt_spec, complexity.MixSpec, test_size)
    #gen_bot.gen_corpus("train", rest_pitt_spec, complexity.MixSpec, train_size)
