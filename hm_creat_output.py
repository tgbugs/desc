class Main :

  def fire(self) :

    if self.inputLength < 0 :
      self.inputLength = self.length.get(0).intValue()

    self.inputs.append(self.in.get(0))
    self.inputLength = self.inputLength - 1

    if self.inputLength == 0 :
      self.processInputs()

    return

  def processInputs(self) :
   
    dbToNifID = {}

    i = 0
    while i < len(self.inputs) :
      recordToken = self.inputs[i]
      termName = recordToken.get("term").stringValue()
      if termName == "error" :
        continue

      id = recordToken.get("id").stringValue()
      self.termToId[termName] = id
      self.idToTerm[id] = termName
      print id + " --> " + termName

      parentId = recordToken.get("parentId").stringValue()
      parentName = self.idToTerm[parentId]

      self.parents[termName] = parentName
      if termName != parentName:
        if parentName not in self.children :
          self.children[parentName] = []
        self.children[parentName].append(termName)
      #print termName + " parent = " + self.parents[termName]
      
      categoryToken = recordToken.get("category")
      dbToken = recordToken.get("db")
      countToken = recordToken.get("count")
      nifIdToken = recordToken.get("nifId")
      indexableToken = recordToken.get("indexable")

      j = 0
      while j < categoryToken.length() :
        catName = categoryToken.getElement(j).stringValue()
        self.categoryNames[catName] = 1

        nifId = nifIdToken.getElement(j).stringValue()
        dbName = dbToken.getElement(j).stringValue()
        indexableName = indexableToken.getElement(j).stringValue()

        if dbName not in dbToNifID :
          dbToNifID[dbName] = nifId
        elif dbToNifID[dbName] != nifId :
          self.duplicateDB[dbName] = 1
          #print "duplicate db " + dbName

        self.dbNames[(dbName, nifId, indexableName)] = 1
        count = int(countToken.getElement(j).stringValue())
        self.dbCounts[(termName, dbName, nifId)] = count

        if (termName, catName) not in self.catCounts :
          self.catCounts[(termName, catName)] = count
        else :
          self.catCounts[(termName, catName)] += count
        #print termName, dbName, self.dbCounts[(termName, dbName)]

        j = j + 1


      i = i + 1

    # determine the level for each term
    for termName in self.termToId.iterkeys() :
      if termName not in self.levels :
        x = self.getLevel(termName)
      else :
        x = self.levels[termName]

    # write outputs
    dbOutToken = self.createDBOutput()
    self.dbOut.broadcast(dbOutToken)

    catOutToken = self.createCategoryOutput()
    self.catOut.broadcast(catOutToken)

    return

  def preinitialize(self):
    self.dbOut.setTypeEquals(BaseType.STRING)
    self.catOut.setTypeEquals(BaseType.STRING)
    self.idToTerm = {}
    self.dbNames = {}
    self.categoryNames = {}
    self.dbCounts = {}
    self.catCounts = {}
    self.parents = {}
    self.children = {}
    self.levels = {}
    self.indentedNames = {}
    self.topTerms = []
    self.maxLevel = -1
    self.duplicateDB = {}
    self.termToId = {}
    self.inputLength = -1
    self.inputs = []

  # create the table for database counts
  def createDBOutput(self):
    t = "<table id='table1'><tr><th></th>"
    for (dbName, nifId, indexable) in sorted(self.dbNames.iterkeys()) :
      t += "<th><a target=\"_blank\" href=\""
      t += "https://neuinfo.org/mynif/databaseList.php?&t=indexable&nif="
      t += nifId + "\">" + dbName
      if dbName in self.duplicateDB :
        t += " (" + indexable + ")"
      t += "</a></th>"
    t += "</tr>"
    for term in sorted(self.topTerms) :
      t += self.outputDepthFirst(term, "db")
    t += "</table>"
    return StringToken(t)    

  # create the table for category counts
  def createCategoryOutput(self):
    t = "<table id='table1'><tr><th></th>"
    for catName in sorted(self.categoryNames.iterkeys()) :
      t += "<th><a target=\"_blank\" href=\""
      t += "https://neuinfo.org/mynif/search.php?q=*&cf=" + catName
      t += "\">" + catName + "</a></th>"
    t += "</tr>"
    for term in sorted(self.topTerms) :
      t += self.outputDepthFirst(term, "category")
    t += "</table>"
    return StringToken(t)

  def getLevel(self, termName) :
    #print "getLevel for " + termName
    if termName not in self.parents :
      level = 1
      self.topTerms.append(termName)
    else :
      parentName = self.parents[termName]
      if parentName == termName :
        level = 1
        self.topTerms.append(termName)
      elif parentName in self.levels :
        level = self.levels[parentName] + 1
      else :
        level = self.getLevel(parentName) + 1

    self.levels[termName] = level
    
    if level > self.maxLevel :
      self.maxLevel = level

    #print termName + " level is " + str(level)
    return level

  def outputDepthFirst(self, term, type) :
    #print "adding " + term
    
    t = "<tr><th align=\"left\"><table><tr>"
    for i in range(1, self.levels[term]) :
      t += "<td>&nbsp;&nbsp;</td>"
    t += "<td><b><a target=\"_blank\" href=\"http://neurolex.org/wiki/"
    t += self.termToId[term] + "\">" + term
    t += "</a></b></td></tr></table></th>"

    if type == "db" :
      for (dbName, nifId, indexable) in sorted(self.dbNames.iterkeys()) :
        if (term, dbName, nifId) not in self.dbCounts :
          t += "<td>0</td>"
        else :
          t += "<td><a target=\"_blank\" href=\"https://neuinfo.org/mynif/search.php?q="
          t += term
          t += "&first=true&t=indexable&nif="
          t += nifId + "\">" + str(self.dbCounts[(term, dbName, nifId)]) + "</a></td>"
    elif type == "category" :
     for catName in sorted(self.categoryNames.iterkeys()) :
        if (term, catName) not in self.catCounts :
          t += "<td>0</td>"
        else :
          t += "<td><a target=\"_blank\" href=\"https://neuinfo.org/mynif/search.php?q="
          t += term + "&cf=" + catName + "\">" + str(self.catCounts[(term, catName)]) + "</a></td>"

    t += "</tr>"
    if term in self.children :
      for childName in sorted(self.children[term]) :
        t += self.outputDepthFirst(childName, type)
    #else :
      #print term + " has no children"

    return t
