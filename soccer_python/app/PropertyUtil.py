import ConfigParser

class PropertyUtil(dict):
  TRUTHY = ['true','True','1']

  def __init__(self, filename):
    cp = ConfigParser.SafeConfigParser()
    cp.optionxform=str
    cp.read(filename)

    for section in cp.sections():
      for option in cp.options(section):
        self[section.replace('/','.')+'.'+option]=cp.get(section,option)

  def getAsString(self, path):
    return self[path]

  def getAsBoolean(self, path):
    return self[path] in PropertyUtil.TRUTHY

  def getAsInt(self, path):
    return int(self[path])

  def getAsFloat(self, path):
    return float(self[path])

  def getAttribute(att):
    return PropertyUtil.properties[att]


