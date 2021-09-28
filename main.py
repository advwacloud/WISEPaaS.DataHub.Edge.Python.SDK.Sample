import datetime
import time
import tkinter 
from tkinter import ttk
from tkinter import messagebox
import string
import random
import threading

from wisepaasdatahubedgesdk.EdgeAgent import EdgeAgent
import wisepaasdatahubedgesdk.Common.Constants as constant
from wisepaasdatahubedgesdk.Model.Edge import EdgeAgentOptions, MQTTOptions, DCCSOptions, EdgeData, EdgeTag, EdgeStatus, EdgeDeviceStatus, EdgeConfig, NodeConfig, DeviceConfig, AnalogTagConfig, DiscreteTagConfig, TextTagConfig
from wisepaasdatahubedgesdk.Common.Utils import RepeatedTimer

class App():

  def __init__(self, master = None):
    self._edgeAgent = None
    self.timer = None
    self.master = master
    master.title('SDK Test')
    master.geometry('580x240')

    # create a tab control
    tabControl = ttk.Notebook(master)
    # create a tab
    dccsTab = ttk.Frame(tabControl, width = 200, height = 100)
    tabControl.add(dccsTab, text = 'DCCS')
    tabControl.grid(column = 0, row = 0, rowspan = 2, columnspan = 2, padx = 8, pady = 4, sticky = 'EWNS')
    # add tab content
    ttk.Label(dccsTab, text = 'API Url:').grid(column = 0, row = 0, sticky = 'EWNS')
    App.apiUrl = tkinter.StringVar()
    tkinter.Entry(dccsTab, textvariable = App.apiUrl, width = 10).grid(column = 1, row = 0, sticky = 'EWNS')
    ttk.Label(dccsTab, text = 'Credential Key:').grid(column = 0, row = 1, sticky = 'EWNS')
    App.credentialKey = tkinter.StringVar()
    tkinter.Entry(dccsTab, textvariable = App.credentialKey, width = 10).grid(column = 1, row = 1, sticky = 'EWNS')

    # create a tab
    mqttTab = ttk.Frame(tabControl, width = 200, height = 100)
    mqttTab.grid(column = 0, row = 0, padx = 8, pady = 4)
    tabControl.add(mqttTab, text = 'MQTT')
    tabControl.grid(column = 0, row = 0, rowspan = 2, columnspan = 2, padx = 8, pady = 4)

    # add tab content
    ttk.Label(mqttTab, text = 'HostName:').grid(column = 0, row = 0, sticky = 'EWNS')
    App.hostName = tkinter.StringVar()
    App.hostName.set('127.0.0.1')
    tkinter.Entry(mqttTab, textvariable = App.hostName, width = 10).grid(column = 1, row = 0, sticky = 'EWNS')
    ttk.Label(mqttTab, text = 'Port:').grid(column = 0, row = 1, sticky = 'EWNS')
    App.port = tkinter.IntVar()
    App.port.set(1883)
    tkinter.Entry(mqttTab, textvariable = App.port, width = 10).grid(column = 1, row = 1, sticky = 'EWNS')
    ttk.Label(mqttTab, text = 'Username:').grid(column = 0, row = 2, sticky = 'EWNS')
    App.userName = tkinter.StringVar()
    App.userName.set('')
    tkinter.Entry(mqttTab, textvariable = App.userName, width = 10).grid(column = 1, row = 2, sticky = 'EWNS')
    ttk.Label(mqttTab, text = 'Password:').grid(column = 0, row = 3, sticky = 'EWNS')
    App.password = tkinter.StringVar()
    App.password.set('')
    tkinter.Entry(mqttTab, textvariable = App.password, width = 10).grid(column = 1, row = 3, sticky = 'EWNS')

    # connect status
    App.status = tkinter.StringVar()
    App.status.set('Disconnected')
    statusLabel = tkinter.Label(master, textvariable = App.status, bg = '#C0C0C0')
    statusLabel.grid(column = 2, row = 0, columnspan = 2, sticky = 'EWNS')

    # function
    def clickedConnect():
      try:
        if App.nodeId.get() == '':
          messagebox.showwarning("Warging", 'nodeId is necessary')
          return
        selectTab = tabControl.tab(tabControl.select(), 'text')
        edgeAgentOptions = EdgeAgentOptions(nodeId = App.nodeId.get())
        if selectTab == 'MQTT':
          edgeAgentOptions.connectType = constant.ConnectType['MQTT']
          mqttOptions = MQTTOptions(hostName = App.hostName.get(), port = App.port.get(), userName = App.userName.get(), password = App.password.get())
          edgeAgentOptions.MQTT = mqttOptions
        elif selectTab == 'DCCS':
          edgeAgentOptions.connectType = constant.ConnectType['DCCS']
          dccsOptions = DCCSOptions(apiUrl = App.apiUrl.get(), credentialKey = App.credentialKey.get())
          edgeAgentOptions.DCCS = dccsOptions
        if self._edgeAgent is None:
          self._edgeAgent = EdgeAgent(edgeAgentOptions)
          self._edgeAgent.on_connected = on_connected
          self._edgeAgent.on_disconnected = on_disconnected
          self._edgeAgent.on_message = on_message
        self._edgeAgent.connect()
      except ValueError as error:
        messagebox.showwarning("Warging", str(error))
    
    def on_connected(edgeAgent, isConnected):
      if isConnected:
        App.status.set('Connected')
        statusLabel.config(bg='#008000')

    def on_disconnected(edgeAgent, isDisconnected):
      if isDisconnected:
        App.status.set('Disconnected')
        statusLabel.config(bg='#C0C0C0')
        self._edgeAgent = None
        self.timer = None

    def on_message(edgeAgent, message):
      if message.type == constant.MessageType['ConfigAck']:
        response = 'Upload Config Result: {0}'.format(str(message.message.result))
        messagebox.showwarning("Information", response)
      elif message.type == constant.MessageType['WriteValue']:
        message = message.message
        for device in message.deviceList:
          print("deviceId: {0}".format(device.id))
          for tag in device.tagList:
            print("tagName: {0}, Value: {1}".format(tag.name, str(tag.value)))
            if device.id == "Device1" and tag.name == "DTag1":
              App.dTag1Value.set(tag.value)

    def clickedDisconnected():
      if self._edgeAgent is None or not self._edgeAgent.isConnected:
        return
      self._edgeAgent.disconnect()

    def clickedSendData():
      if self._edgeAgent is None or not self._edgeAgent.isConnected:
        messagebox.showwarning("Warging", 'edge not connected')
        return
      frequency = int(App.frequency.get())
      if self.timer is None:
        self.timer = RepeatedTimer(frequency, __sendData)
        __sendData()

    def __sendData():
      data = __generateData()
      self._edgeAgent.sendData(data)

    def clickedDeviceStatus():
      if self._edgeAgent is None or not self._edgeAgent.isConnected:
        messagebox.showwarning("Warging", 'edge not connected')
        return
      status = __generateStatus()
      self._edgeAgent.sendDeviceStatus(status)

    def clickedUploadConfig():
      if self._edgeAgent is None or not self._edgeAgent.isConnected:
        messagebox.showwarning("Warging", 'edge not connected')
        return
      config = __generateConfig()
      self._edgeAgent.uploadConfig(action = constant.ActionType['Create'], edgeConfig = config)

    def clickedUpdateConfig():
      if self._edgeAgent is None or not self._edgeAgent.isConnected:
        messagebox.showwarning("Warging", 'edge not connected')
        return
      config = __generateConfig()
      self._edgeAgent.uploadConfig(action = constant.ActionType['Update'], edgeConfig = config)

    def clickedDeleteNode():
      if self._edgeAgent is None or not self._edgeAgent.isConnected:
        messagebox.showwarning("Warging", 'edge not connected')
        return
      config = __generateDelteNodeConfig()
      self._edgeAgent.uploadConfig(action = constant.ActionType['Delete'], edgeConfig = config)

    def clickedDeleteDevice():
      if self._edgeAgent is None or not self._edgeAgent.isConnected:
        messagebox.showwarning("Warging", 'edge not connected')
        return
      config = __generateDelteDeviceConfig()
      self._edgeAgent.uploadConfig(action = constant.ActionType['Delete'], edgeConfig = config)

    def clickedDeleteTag():
      if self._edgeAgent is None or not self._edgeAgent.isConnected:
        messagebox.showwarning("Warging", 'edge not connected')
        return
      config = __generateDelteTagConfig()
      self._edgeAgent.uploadConfig(action = constant.ActionType['Delete'], edgeConfig = config)

    def __generateBatchData():  # send data in batch for high frequency data
      array = []
      for n in range(1, 10):
        edgeData = EdgeData()
        for i in range(1, int(App.deviceCount.get()) + 1):
          for j in range(1, int(App.analogCount.get()) + 1):
            deviceId = 'Device' + str(i)
            tagName = 'ATag' + str(j)
            value = random.uniform(0, 100)
            tag = EdgeTag(deviceId, tagName, value)
            edgeData.tagList.append(tag)
          for j in range(1, int(App.discreteCount.get()) + 1):
            deviceId = 'Device' + str(i)
            tagName = 'DTag' + str(j)
            value = random.randint(0,99)
            value = value % 2
            tag = EdgeTag(deviceId, tagName, value)
            edgeData.tagList.append(tag)
          for j in range(1, int(App.textCount.get()) + 1):
            deviceId = 'Device' + str(i)
            tagName = 'TTag' + str(j)
            value = random.uniform(0, 100)
            value = 'TEST ' + str(value)
            tag = EdgeTag(deviceId, tagName, value)
            edgeData.tagList.append(tag)

        edgeData.timestamp = datetime.datetime.now()
        array.append(edgeData)
      return array

    def __generateData():
      edgeData = EdgeData()
      for i in range(1, int(App.deviceCount.get()) + 1):
        for j in range(1, int(App.analogCount.get()) + 1):
          deviceId = 'Device' + str(i)
          tagName = 'ATag' + str(j)
          value = random.uniform(0, 100)
          tag = EdgeTag(deviceId, tagName, value)
          edgeData.tagList.append(tag)
        for j in range(1, int(App.discreteCount.get()) + 1):
          deviceId = 'Device' + str(i)
          tagName = 'DTag' + str(j)
          value = random.randint(0,99)
          value = value % 2
          tag = EdgeTag(deviceId, tagName, value)
          edgeData.tagList.append(tag)
        for j in range(1, int(App.textCount.get()) + 1):
          deviceId = 'Device' + str(i)
          tagName = 'TTag' + str(j)
          value = random.uniform(0, 100)
          value = 'TEST ' + str(value)
          tag = EdgeTag(deviceId, tagName, value)
          edgeData.tagList.append(tag)

      edgeData.timestamp = datetime.datetime.now()
      #edgeData.timestamp = datetime.datetime(2020,8,24,6,10,8)  # you can defne the timestamp(local time) of data 
      return edgeData

    def __generateStatus():
      deviceStatus = EdgeDeviceStatus()
      for i in range(1, int(App.deviceCount.get()) + 1):
        deviceId = 'Device' + str(i)
        device = EdgeStatus(id = deviceId, status = constant.Status['Online'])
        deviceStatus.deviceList.append(device)
      return deviceStatus

    def __generateConfig():
      config = EdgeConfig()
      nodeConfig = NodeConfig(nodeType = constant.EdgeType['Gateway'])
      config.node = nodeConfig
      for i in range(1, int(App.deviceCount.get()) + 1):
        deviceConfig = DeviceConfig(id = 'Device' + str(i),
          name = 'Device' + str(i),
          description = 'Device' + str(i),
          deviceType = 'Smart Device',
          retentionPolicyName = '')
        for j in range(1, int(App.analogCount.get()) + 1):
          analog = AnalogTagConfig(name = 'ATag' + str(j),
            description = 'ATag ' + str(j),
            readOnly = False,
            arraySize = 0,
            spanHigh = 1000,
            spanLow = 0,
            engineerUnit = '',
            integerDisplayFormat = 4,
            fractionDisplayFormat = 2)
          deviceConfig.analogTagList.append(analog)
        for j in range(1, int(App.discreteCount.get()) + 1):
          discrete = DiscreteTagConfig(name = 'DTag' + str(j),
            description = 'DTag ' + str(j),
            readOnly = False,
            arraySize = 0,
            state0 = '0',
            state1 = '1')
          deviceConfig.discreteTagList.append(discrete)
        for j in range(1, int(App.textCount.get()) + 1):
          text = TextTagConfig(name = 'TTag' + str(j),
            description = 'TTag ' + str(j),
            readOnly = False,
            arraySize = 0)
          deviceConfig.textTagList.append(text)
        config.node.deviceList.append(deviceConfig)
      return config

    def __generateDelteNodeConfig():
      config = EdgeConfig()
      nodeConfig = NodeConfig()
      config.node = nodeConfig
      return config

    def __generateDelteDeviceConfig():
      config = EdgeConfig()
      nodeConfig = NodeConfig()
      config.node = nodeConfig
      for i in range(1, int(App.deviceCount.get()) + 1):
        deviceConfig = DeviceConfig(id = 'Device' + str(i))
        config.node.deviceList.append(deviceConfig)
      return config

    def __generateDelteTagConfig():
      config = EdgeConfig()
      nodeConfig = NodeConfig()
      config.node = nodeConfig
      for i in range(1, int(App.deviceCount.get()) + 1):
        deviceConfig = DeviceConfig(id = 'Device' + str(i))
        for j in range(1, int(App.analogCount.get()) + 1):
          analog = AnalogTagConfig(name = 'ATag' + str(j))
          deviceConfig.analogTagList.append(analog)
        for j in range(1, int(App.discreteCount.get()) + 1):
          discrete = DiscreteTagConfig(name = 'DTag' + str(j))
          deviceConfig.discreteTagList.append(discrete)
        for j in range(1, int(App.textCount.get()) + 1):
          text = TextTagConfig(name = 'TTag' + str(j))
          deviceConfig.textTagList.append(text)
        config.node.deviceList.append(deviceConfig)
      return config

    # input
    nodeFrame = tkinter.Frame(master)
    nodeFrame.grid(column = 0, row = 2, columnspan = 2, sticky = 'W')
    ttk.Label(nodeFrame, text = 'NodeId:').pack(side = tkinter.TOP)
    App.nodeId = tkinter.StringVar()
    tkinter.Entry(nodeFrame, textvariable = App.nodeId, width = 10).pack(side = tkinter.TOP)
    wvFrame = tkinter.Frame(master)
    wvFrame.grid(column = 1, row = 2, columnspan = 2, sticky = 'W')
    ttk.Label(wvFrame, text = 'DTag1 Value:').pack(side = tkinter.TOP)
    App.dTag1Value = tkinter.IntVar()
    App.dTag1Value.set(1)
    ttk.Label(wvFrame, textvariable = App.dTag1Value).pack(side = tkinter.TOP)
    deviceFrame = tkinter.Frame(master)
    deviceFrame.grid(column = 0, row = 3, columnspan = 2, sticky = 'W')
    ttk.Label(deviceFrame, text = 'Device Count:').pack(side = tkinter.TOP)
    App.deviceCount = tkinter.IntVar()
    App.deviceCount.set(1)
    tkinter.Entry(deviceFrame, textvariable = App.deviceCount, width = 10).pack(side = tkinter.TOP)
    analogFrame = tkinter.Frame(master)
    analogFrame.grid(column = 0, row = 4, sticky = 'EWNS')
    ttk.Label(analogFrame, text = 'Analog Tag Count:').pack(side = tkinter.TOP)
    App.analogCount = tkinter.IntVar()
    App.analogCount.set(5)
    tkinter.Entry(analogFrame, textvariable = App.analogCount, width = 10).pack(side = tkinter.TOP)
    discreteFrame = tkinter.Frame(master)
    discreteFrame.grid(column = 1, row = 4, sticky = 'EWNS')
    ttk.Label(discreteFrame, text = 'Discrete Tag Count:').pack(side = tkinter.TOP)
    App.discreteCount = tkinter.IntVar()
    App.discreteCount.set(5)
    tkinter.Entry(discreteFrame, textvariable = App.discreteCount, width = 10).pack(side = tkinter.TOP)
    textFrame = tkinter.Frame(master)
    textFrame.grid(column = 2, row = 4, sticky = 'EWNS')
    ttk.Label(textFrame, text = 'Text Tag Count:').pack(side = tkinter.TOP)
    App.textCount = tkinter.IntVar()
    App.textCount.set(5)
    tkinter.Entry(textFrame, textvariable = App.textCount, width = 10).pack(side = tkinter.TOP)
    fraquencyFrame = tkinter.Frame(master)
    fraquencyFrame.grid(column = 3, row = 4, sticky = 'EWNS')
    ttk.Label(fraquencyFrame, text = 'Data Fredquency:').pack(side = tkinter.TOP)
    App.frequency = tkinter.IntVar()
    App.frequency.set(1)
    tkinter.Entry(fraquencyFrame, textvariable = App.frequency, width = 10).pack(side = tkinter.TOP)

    # button
    ttk.Button(master, text = 'Connect', command = clickedConnect).grid(column = 2, row = 1, sticky = 'EWNS')
    ttk.Button(master, text = 'Disconnect', command = clickedDisconnected).grid(column = 3, row = 1, sticky = 'EWNS')
    ttk.Button(master, text = 'Update Device Status', command = clickedDeviceStatus).grid(column = 2, row = 2, sticky = 'EWNS')
    ttk.Button(master, text = 'Send Data', command = clickedSendData).grid(column = 3, row = 2, sticky = 'EWNS')
    ttk.Button(master, text = 'Upload Config', command = clickedUploadConfig).grid(column = 4, row = 0, sticky = 'EWNS')
    ttk.Button(master, text = 'Update Config', command = clickedUpdateConfig).grid(column = 4, row = 1, sticky = 'EWNS')
    ttk.Button(master, text = 'Delete All Config', command = clickedDeleteNode).grid(column = 4, row = 2, sticky = 'EWNS')
    ttk.Button(master, text = 'Delete Devices', command = clickedDeleteDevice).grid(column = 4, row = 3, sticky = 'EWNS')
    ttk.Button(master, text = 'Delete Tag', command = clickedDeleteTag).grid(column = 4, row = 4, sticky = 'EWNS')

root = tkinter.Tk()
mainWindow = App(root)

root.mainloop() # start GUI