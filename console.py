import datetime
import time
import string
import random
import threading

from wisepaasdatahubedgesdk.EdgeAgent import EdgeAgent
import wisepaasdatahubedgesdk.Common.Constants as constant
from wisepaasdatahubedgesdk.Model.Edge import EdgeAgentOptions, MQTTOptions, DCCSOptions, EdgeData, EdgeTag, EdgeStatus, EdgeDeviceStatus, EdgeConfig, NodeConfig, DeviceConfig, AnalogTagConfig, DiscreteTagConfig, TextTagConfig
from wisepaasdatahubedgesdk.Common.Utils import RepeatedTimer


def on_connected(edgeAgent, isConnected):
  config = __generateConfig()
  _edgeAgent.uploadConfig(action = constant.ActionType['Create'], edgeConfig = config)
  for i in range(1, 60):
    __sendData()
    time.sleep(1)
  
def on_disconnected(edgeAgent, isDisconnected):
  print("disconnected !")

def edgeAgent_on_message(agent, messageReceivedEventArgs):
  print("edgeAgent_on_message !")

def __sendData():
  data = __generateData()
  _edgeAgent.sendData(data)


def __generateData():
  edgeData = EdgeData()
  for i in range(1, 1 + 1):
    for j in range(1, 1 + 1):
      deviceId = 'Device' + str(i)
      tagName = 'ATag' + str(j)
      value = random.uniform(0, 100)
      tag = EdgeTag(deviceId, tagName, value)
      edgeData.tagList.append(tag)
    for j in range(1, 1 + 1):
      deviceId = 'Device' + str(i)
      tagName = 'DTag' + str(j)
      value = random.randint(0,99)
      value = value % 2
      tag = EdgeTag(deviceId, tagName, value)
      edgeData.tagList.append(tag)
    for j in range(1, 1 + 1):
      deviceId = 'Device' + str(i)
      tagName = 'TTag' + str(j)
      value = random.uniform(0, 100)
      value = 'TEST ' + str(value)
      tag = EdgeTag(deviceId, tagName, value)
      edgeData.tagList.append(tag)

  return edgeData

def __generateConfig():
  config = EdgeConfig()
  deviceConfig = DeviceConfig(id = 'Device1',
    name = 'Device1',
    description = 'Device1',
    deviceType = 'Smart Device1',
    retentionPolicyName = '')
  
  analog = AnalogTagConfig(name = 'ATag1',
    description = 'ATag1',
    readOnly = False,
    arraySize = 0,
    spanHigh = 1000,
    spanLow = 0,
    engineerUnit = '',
    integerDisplayFormat = 4,
    fractionDisplayFormat = 2)
  deviceConfig.analogTagList.append(analog)

  discrete = DiscreteTagConfig(name = 'DTag1',
    description = 'DTag1',
    readOnly = False,
    arraySize = 0,
    state0 = 'Stop',
    state1 = 'Start')
  deviceConfig.discreteTagList.append(discrete)
  
  text = TextTagConfig(name = 'TTag1',
    description = 'TTag1',
    readOnly = False,
    arraySize = 0)
  deviceConfig.textTagList.append(text)

  config.node.deviceList.append(deviceConfig)
  return config


_edgeAgent = None
edgeAgentOptions = EdgeAgentOptions(nodeId = '5d332422-6751-40f7-ac15-44c52e6de9f5')
edgeAgentOptions.connectType = constant.ConnectType['DCCS']
dccsOptions = DCCSOptions(apiUrl = 'https://api-dccs-ensaas.sa.wise-paas.com/', credentialKey = 'f8e6a12ad857618f435e95665ddb43u3')
edgeAgentOptions.DCCS = dccsOptions
_edgeAgent = EdgeAgent(edgeAgentOptions)
_edgeAgent.on_connected = on_connected
_edgeAgent.on_disconnected = on_disconnected
_edgeAgent.on_message = edgeAgent_on_message

_edgeAgent.connect()

time.sleep(10)  # wait for connecting to avoid process closing directly
