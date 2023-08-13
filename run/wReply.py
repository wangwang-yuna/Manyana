# -*- coding: utf-8 -*-
import datetime
import json
import random
import re
import sys

import os
from asyncio import sleep

import httpx
import requests
import yaml
from fuzzywuzzy import process
from mirai import Mirai, FriendMessage, WebSocketAdapter, GroupMessage, Startup
from mirai import Image, Voice
from mirai import Mirai, WebSocketAdapter, FriendMessage, GroupMessage, At, Plain

from plugins.RandomStr import random_str
from plugins.imgDownload import dict_download_img
from plugins.modelsLoader import modelLoader
from plugins.translater import translate
from plugins.vitsGenerate import voiceGenerate
from plugins.wReply.mohuReply import mohuaddReplys, mohudels, mohuadd
from plugins.wReply.superDict import outPutDic, importDict


def main(bot,config,sizhiKey,app_id, app_key,logger):
    logger.info("启动自定义词库")
    logger.info("自定义词库读取配置文件")
    #读取配置文件
    with open('config/autoSettings.yaml', 'r', encoding='utf-8') as f:
        result = yaml.load(f.read(), Loader=yaml.FullLoader)
    global blUser
    blUser=result.get("banUser")
    global blGroup
    blGroup = result.get("banGroups")
    with open('config/noResponse.yaml', 'r', encoding='utf-8') as f:
        noRes1 = yaml.load(f.read(), Loader=yaml.FullLoader)
        noRes=noRes1.get("noRes")
    with open('config/settings.yaml', 'r', encoding='utf-8') as f:
        result = yaml.load(f.read(), Loader=yaml.FullLoader)
    global yamlData
    yamlData = result.get("wReply")
    global chineseVoiceRate
    chineseVoiceRate = yamlData.get("chineseVoiceRate")
    global voiceRate
    voiceRate = yamlData.get("voiceRate")
    # 过滤词库
    global ban
    ban = yamlData.get("banWords")
    # 不艾特回复的几率
    global likeindex
    likeindex = yamlData.get("replyRate")
    global groupLexicon
    groupLexicon=yamlData.get("groupLexicon")
    global sizhi
    sizhi = yamlData.get("sizhi")
    global turnMess
    turnMess = yamlData.get("turnMessage")



    file = open('config/superDict.txt', 'r')
    jss = file.read()
    file.close()

    global superDict
    superDict = json.loads(jss)

    with open('data/userData.yaml', 'r',encoding='utf-8') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    global trustUser
    global userdict
    userdict = data
    trustUser = []
    for i in userdict.keys():
        data = userdict.get(i)
        times = int(str(data.get('sts')))
        if times > 14:
            trustUser.append(str(i))

    logger.info('已读取信任用户' + str(len(trustUser)) + '个')

    #修改为你bot的名字
    global botName
    botName = config.get('botName')
    #你的QQ
    global master
    master=int(config.get('master'))

    with open('config/nudgeReply.yaml', 'r', encoding='utf-8') as f:
        result232 = yaml.load(f.read(), Loader=yaml.FullLoader)

    global modelSelect
    global speaker
    speaker = result232.get("defaultModel").get("speaker")
    modelSelect = result232.get("defaultModel").get("modelSelect")

    logger.info("当前语音模型设定："+str(speaker)+"\n模型"+str(modelSelect))
    global models
    global characters
    models, default, characters = modelLoader()  # 读取模型

    @bot.on(GroupMessage)
    async def setDefaultModel(event: GroupMessage):
        if event.sender.id == master and str(event.message_chain).startswith("设定角色#"):
            global speaker
            global modelSelect
            if str(event.message_chain).split("#")[1] in characters:
                speaker1 = str(event.message_chain).split("#")[1]
                speaker = int(characters.get(speaker1)[0])
                modelSelect = characters.get(speaker1)[1]

    #下面的是一堆乱七八糟的变量


    global process1
    process1={}
    global inprocess1
    inprocess1={}

    @bot.on(GroupMessage)
    async def handle_group_message(event: GroupMessage):
        if str(event.message_chain) == '开始添加':
            if (str(event.sender.id) in trustUser or event.sender.id==master) and event.sender.id not in blUser:
                global process1
                if str(event.sender.group.id) not in superDict.keys():
                    await bot.send(event,"无本群专有词库，创建中.....")
                await bot.send(event, '请输入关键词')
                process1[event.sender.id] = {"process": 1}
            else:
                await bot.send(event,event.sender.member_name+'没有添加的权限哦....')


    @bot.on(GroupMessage)
    async def handle_group_message(event: GroupMessage):
        global ban
        global process1
        if event.sender.id in process1 and process1.get(event.sender.id).get("process") == 1 and str(event.message_chain)!="over":
            '''if event.message_chain.count(Image) == 1:
                lst_img = event.message_chain.get(Image)
                mohukey = str(lst_img[0].url)
                print(mohukey)
                await bot.send(event, '已记录关键词,请发送回复(发送over结束添加)')
                mohustatus = 2
            checkResult=await checkIfOk(str(event.message_chain),event)
            if checkResult==False:
                await bot.send(event,"检测到违禁词")
            else:'''
            await bot.send(event, '已记录关键词,请发送回复(发送over结束添加)\n文本回复前缀 语音 可以设置为语音回复')
            process1[event.sender.id] = {"process": 2, "mohukey": str(event.message_chain),"groupId":event.group.id}


    @bot.on(GroupMessage)
    async def handle_group_message(event: GroupMessage):
        global ban
        global process1
        if event.sender.id in process1 and process1.get(event.sender.id).get("process") == 2:
            if event.sender.id in process1 and str(event.message_chain)!="over":
                '''checkResult = await checkIfOk(str(event.message_chain),event)
                if checkResult == False:
                    await bot.send(event, "检测到违禁词")
                else:'''
                if 1:
                    if str(event.message_chain).startswith("语音"):
                        logger.info("增加语音回复")
                        ranpath = random_str()
                        path ='../data/autoReply/voiceReply/' + ranpath + '.wav'
                        text = await translate(str(event.message_chain)[2:], app_id, app_key)
                        tex = '[JA]' + text + '[JA]'
                        await voiceGenerate({"text":tex,"out":path,"speaker":speaker,"modelSelect":modelSelect})
                        value = ranpath + '.wav'
                    elif event.message_chain.count(Image) == 1:
                        logger.info("增加图片回复")
                        lst_img = event.message_chain.get(Image)
                        url = lst_img[0].url
                        imgname = dict_download_img(url,"data/autoReply/imageReply")
                        value = imgname.replace("data/autoReply/imageReply/","")
                        if value.endswith(".jpg"):
                            pass
                        else:
                            value+=".jpg"
                    else:
                        logger.info("增加文本回复")
                        value = str(event.message_chain)
                    global superDict
                    addStr = '添加' + process1.get(event.sender.id).get("mohukey") + '#' + value
                    superDict = mohuaddReplys(addStr,str(event.group.id))
                    await bot.send(event, '已添加至词库')
                    outPutDic(str(event.group.id))

    @bot.on(GroupMessage)
    async def init(event: GroupMessage):
        global process1
        if event.sender.id in process1 and str(event.message_chain) == "over":
            process1.pop(event.sender.id)
            await bot.send(event,"结束添加")


    # 模糊词库触发回复
    @bot.on(GroupMessage)
    async def mohu(event: GroupMessage):
        global superDict,botName,likeindex,temp,sizhi
        if At(bot.qq) in event.message_chain:
            for i in noRes:
                if i in str(event.message_chain):
                    return
            getStr = str(event.message_chain).replace("@"+str(bot.qq)+" ", '')
        else:
            getStr = str(event.message_chain)

        if sizhi==True:
            sess = requests.get('https://api.ownthink.com/bot?spoken=' + getStr + '&appid='+random.choice(sizhiKey))
            answer = sess.text
            try:
                answer = json.loads(answer)
            except:
                logger.warning("在调用思知ai时出现了一个问题，但似乎又没啥问题，请忽略")
                return
            logger.info("ASK:"+getStr)
            logger.info("bot(思知):" + answer.get("data").get("info").get("text"))
            replyssssss=answer.get("data").get("info").get("text")
        else:
            #优先匹配本词库
            if str(event.group.id) in superDict.keys():
                if random.randint(0,100)<groupLexicon or At(bot.qq) in event.message_chain:
                    keys1=superDict.get(str(event.group.id)).keys()
                    lock=0
                    for i in keys1:
                        pat=i.split("/")
                        pattern=""
                        for patts in pat:
                            pattern+=".*"+patts
                        pattern+=".*"
                        logger.warning("生成正则表达式"+pattern)
                        match = re.search(pattern, getStr)
                        if match:
                            replyssssss=random.choice(superDict.get(str(event.group.id)).get(str((i))))
                            lock=1
                            break
                    if lock==0:
                        if At(bot.qq) in event.message_chain and random.randint(0,100)<likeindex:
                            best_matches = process.extractBests(getStr, superDict.get("public").keys(), limit=3)
                            logger.info("获取匹配结果：key:" + getStr + "|" + str(best_matches))
                            replyssssss = random.choice(superDict.get("public").get(str((best_matches)[0][0])))
                        else:
                            return
                else:
                    return

            elif random.randint(0,100)<likeindex:
                #best_match = process.extractOne(getStr, superDict.keys())
                best_matches = process.extractBests(getStr, superDict.get("public").keys(), limit=3)
                logger.info("获取匹配结果：key:" + getStr + "|" + str(best_matches))
                replyssssss =random.choice(superDict.get("public").get(str((best_matches)[0][0])))
            else:
                return
        logger.info("key:："+getStr+" 选择回复：" + replyssssss)

        if str(replyssssss).endswith('.png') or str(replyssssss).endswith('.jpg'):
            await bot.send(event, Image(path='data/autoReply/imageReply/' + replyssssss))
        elif str(replyssssss).endswith('.wav'):
            await bot.send(event, Voice(path='data/autoReply/voiceReply/' + replyssssss))
        else:

            replyssssss = replyssssss.replace("{me}", botName).replace("yucca", botName).replace("小思",  botName).replace("{segment}", ',')

            if str(event.sender.id) not in userdict:
                replyssssss = replyssssss.replace("name", str(event.sender.member_name)).replace("{name}", str(event.sender.member_name)).replace("哥哥", str(event.sender.member_name)).replace("您", str(event.sender.member_name))
            else:

                setName = userdict.get(str(event.sender.id)).get("userName")
                if setName==None:
                    setName=event.sender.member_name
                replyssssss = replyssssss.replace("name", setName).replace("{name}", setName).replace("哥哥", setName).replace("您", setName)

            if random.randint(1, 100) > voiceRate:
                await bot.send(event, replyssssss)
            else:
                replyssssss = replyssssss.replace(botName, "我")
                path = '../data/voices/' + random_str() + '.wav'
                if random.randint(1,100)>chineseVoiceRate:
                    text=await translate(str(replyssssss), app_id, app_key)
                    tex = '[JA]' + text + '[JA]'
                else:
                    tex="[ZH]"+replyssssss+"[ZH]"
                logger.info("启动文本转语音：text: "+tex+" path: "+path[3:])
                await voiceGenerate({"text": tex, "out": path,"speaker":speaker,"modelSelect":modelSelect})
                await bot.send(event,Voice(path=path[3:]))
    # 开启和关闭思知ai
    @bot.on(GroupMessage)
    async def sizhiOpener(event:GroupMessage):
        if str(event.message_chain)=="sizhi" and event.sender.id==master:
            global sizhi
            if sizhi==0:
                sizhi=1
                await bot.send(event,"已开启思知ai")
            else:
                sizhi=0
                await bot.send(event,"关闭思知ai")

    # 取消注释开放私聊
    @bot.on(FriendMessage)
    async def mohu(event: FriendMessage):
        global superDict
        global botName
        global sizhi
        if event.sender.id in blUser:
            return
        getStr=str(event.message_chain)
        if sizhi==True:
            sess = requests.get(
                'https://api.ownthink.com/bot?spoken=' + getStr + '&appid='+random.choice(sizhiKey))

            answer = sess.text
            try:
                answer = json.loads(answer)
            except:
                logger.warning("在调用思知ai时出现了一个问题，但似乎又没啥问题，请忽略")
                return
            logger.info("ASK:"+getStr)
            logger.info("bot(私聊):" + answer.get("data").get("info").get("text"))
            replyssssss = answer.get("data").get("info").get("text")
        else:

            if event.sender.id==bot.qq:
                return
            best_matches = process.extractBests(getStr, superDict.get("public").keys(), limit=3)
            logger.info("获取匹配结果：key:" + getStr + "|" + str(best_matches))
            replyssssss = random.choice(superDict.get("public").get(str((best_matches)[0][0])))
            logger.info("key:：" + getStr + " 选择回复：" + replyssssss)

        if str(replyssssss).endswith('.png') or str(replyssssss).endswith('.jpg'):
            await bot.send(event, Image(path='data/autoReply/imageReply/' + replyssssss))
        elif str(replyssssss).endswith('.wav'):
            return
        else:
            replyssssss = replyssssss.replace("小思", botName).replace("{me}", botName).replace("yucca", botName).replace("{segment}", ',')
            if str(event.sender.id) not in userdict:
                replyssssss=replyssssss.replace("name", str(event.sender.nickname)).replace("{name}", str(event.sender.nickname)).replace("哥哥", str(event.sender.nickname))
            else:
                setName=userdict.get(str(event.sender.id)).get("userName")
                if setName==None:
                    setName=event.sender.nickname
                replyssssss=replyssssss.replace("name", setName).replace("{name}", setName).replace("哥哥", setName)

            logger.info('接收私聊消息,来自' + str(event.sender.get_name()) + ' | ' + str(
                event.sender.id) + '内容：' + event.message_chain)
            global turnMess
            if turnMess == True and event.sender.id != master:
                await bot.send_friend_message(master,'接收私聊消息\n来自：' + str(event.sender.get_name()) + '\nQQ:' + str(event.sender.id) + '\n内容：' + event.message_chain + '\n用--> ' + replyssssss + ' <--回复了')
            else:
                pass
            await bot.send(event, replyssssss)


    @bot.on(FriendMessage)
    async def banTurnMess(event: FriendMessage):
        global turnMess
        if str(event.sender.id)==str(master):
            if str(event.message_chain)=='关闭转发':
                await bot.send(event,'已关闭转发')
                logger.info("关闭私聊转发")
                turnMess=False
            elif str(event.message_chain)=='开启转发':
                logger("开启私聊转发")
                await bot.send(event, '已开启转发')
                turnMess=True

    # 删除模糊回复value
    @bot.on(GroupMessage)
    async def dele(event: GroupMessage):
        if str(event.message_chain).startswith('删除#'):
            global superDict
            if str(event.sender.id) in trustUser or event.sender.id==master or str(event.sender.group.id) in superDict.keys():
                logger.warning("准备删除")
                s1 = str(event.message_chain).split('#')
                aimStr = s1[1]
                lis1=[]

                if aimStr in superDict.get(str(event.group.id)).keys():
                    replyMes = superDict.get(str(event.group.id)).get(aimStr)
                    number = 0
                    for i in replyMes:

                        if i.endswith('.png'):
                            await bot.send(event, ('编号:' + str(number),Image(path='data/autoReply/imageReply/' + i)))
                        elif i.endswith('.wav'):
                            await bot.send(event, '编号:' + str(number))
                            await bot.send(event, Voice(path='data/autoReply/voiceReply/' + i))
                        else:
                            await bot.send(event, '编号:' + str(number)+"\n"+i)
                        number += 1
                    global inprocess1
                    inprocess1[event.sender.id]={"delStr":aimStr,"step":1}
                    await bot.send(event, '请发送要删除的序号')

            else:
                await bot.send(event, event.sender.member_name + '似乎没有删除的权限呢...')


    # 删除指定下标执行部分
    @bot.on(GroupMessage)
    async def handle_group_message(event: GroupMessage):
        global superDict
        global inprocess1
        if event.sender.id in inprocess1 and inprocess1.get(event.sender.id).get("step") == 1:
                replyMes = superDict.get(str(event.group.id)).get(inprocess1.get(event.sender.id).get("delStr"))
                try:
                    logger.warning("执行自定义回复删除操作")
                    '''i=replyMes[int(str(event.message_chain))]
                    if i.endswith('.png'):
                        path='data/autoReply/imageReply/' + i
                    elif i.endswith('.wav'):
                        path='data/autoReply/voiceReply/' + i'''
                    del replyMes[int(str(event.message_chain))]
                    #os.remove(path)
                    superDict = mohuadd(inprocess1.get(event.sender.id).get("delStr"), replyMes,str(event.group.id))
                    logger.info("完成删除回复操作")
                    await bot.send(event, '已删除')
                except:
                    await bot.send(event, '下标不合法')
                inprocess1.pop(event.sender.id)
                outPutDic(str(event.group.id))




    @bot.on(GroupMessage)
    async def restarts(event: GroupMessage):
        if str(event.message_chain)=='导入词库' and str(event.sender.id)==str(master):
            importDict()
            file = open('config/superDict.txt', 'r')
            jss = file.read()
            file.close()
            global superDict
            superDict = json.loads(jss)

            print('已读取模糊匹配字典')
            await bot.send(event, '已导入')



    '''@bot.on(GroupMessage)
    async def restarts(event: GroupMessage):
        if str(event.message_chain) == '导出词库' and str(event.sender.id) == str(master):
            outPutDic()
            await bot.send(event, '已导出')'''
    @bot.on(Startup)
    async def updateData(event: Startup):
        while True:
            await sleep(360)
            logger.info("开始更新数据")
            with open('config/autoSettings.yaml', 'r', encoding='utf-8') as f:
                result = yaml.load(f.read(), Loader=yaml.FullLoader)
            global blUser
            blUser = result.get("banUser")
            global blGroup
            blUser = result.get("banGroups")
            with open('config/settings.yaml', 'r', encoding='utf-8') as f:
                result = yaml.load(f.read(), Loader=yaml.FullLoader)
            global yamlData
            yamlData = result.get("wReply")
            global voiceRate
            voiceRate = yamlData.get("voiceRate")
            # 过滤词库
            global ban
            ban = yamlData.get("banWords")
            # 不艾特回复的几率
            global likeindex
            likeindex = yamlData.get("replyRate")
            global sizhi
            sizhi = yamlData.get("sizhi")
            global turnMess
            turnMess = yamlData.get("turnMessage")

            global modelSelect
            global speaker
            speaker=result.get("defaultModel").get("speaker")
            modelSelect=result.get("defaultModel").get("modelSelect")

            file = open('config/superDict.txt', 'r')
            jss = file.read()
            file.close()
            global superDict
            superDict = json.loads(jss)

            with open('data/userData.yaml', 'r',encoding='utf-8') as file:
                data = yaml.load(file, Loader=yaml.FullLoader)
            global trustUser
            global userdict
            userdict = data
            trustUser = []
            for i in userdict.keys():
                data = userdict.get(i)
                times = int(str(data.get('sts')))
                if times > 10:
                    trustUser.append(str(i))

            logger.info('已读取信任用户' + str(len(trustUser)) + '个')
    @bot.on(GroupMessage)
    async def nameChangeOperatot(event:GroupMessage):
        global userdict
        msg = "".join(map(str, event.message_chain[Plain]))
        # 匹配指令
        m = re.match(r'^name\s*(\w+)\s*$', msg.strip())
        if m:
            # 取出指令中的地名
            name = m.group(1)
            for i in ban:
                if i in name:
                    await bot.send(event,"检测到违禁词汇,操作中止")
                    return
            if str(event.sender.id) in userdict:
                data=userdict.get(str(event.sender.id))
                data["userName"]=name
                userdict[str(event.sender.id)]=data
                with open('data/userData.yaml', 'w',encoding="utf-8") as file:
                    yaml.dump(userdict, file, allow_unicode=True)
                logger.info(str(event.sender.id)+"更改了称谓："+name)
                await bot.send(event,"对您的称呼已变更为："+name)
            else:
                await bot.send(event,str(event.sender.member_name)+"还不是用户...发送 签到 试试吧")


    async def checkIfOk(str1,event):
        if event.group.id in blGroup:
            return False
        if event.sender.id in blUser:
            return False
        for i in ban:
            if i in str1:
                return False
        return True




