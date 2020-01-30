#!/usr/bin/env python
# BNM Project
# Manage configuration files 
# Created by Yuriy M. Plyaskin 2008.04
# Modify 2009.11 - Ver. 0.2
# Modify 2010.04 - Ver. 0.3

import sys
import os
from stat import ST_SIZE
import time
#import popen2
import subprocess
from PyQt4 import QtCore, QtGui, QtXml
import bnm_rc

class QViewLog (QtGui.QDialog):
   def __init__(self, text, parent=None):
      QtGui.QDialog.__init__(self, parent)
      
      q_viewLayout = QtGui.QVBoxLayout()
      q_doc = QtGui.QTextEdit()
      q_doc.setReadOnly(True)
      q_doc.setPlainText(text)
      q_viewLayout.addWidget(q_doc)
      q_buttonLayout = QtGui.QHBoxLayout()
      q_buttonLayout.addStretch()
      q_buttonDone = QtGui.QPushButton(u'Done')
      q_buttonLayout.addWidget(q_buttonDone)
      q_viewLayout.addLayout(q_buttonLayout)
      self.setWindowTitle(u'Script StdOut/StdErr')
      self.setLayout(q_viewLayout)
      
      self.connect(q_buttonDone,QtCore.SIGNAL("clicked()"),self,QtCore.SLOT("reject()"))

class QGetRunThread (QtCore.QThread):
   def run(self):
      global BNMDialog
      for i in xrange(0, BNMDialog.q_mainTree.topLevelItemCount()):
         q_host = BNMDialog.q_mainTree.topLevelItem(i)
         if BNMDialog.q_mainTree.itemWidget(q_host.child(3),1).checkState() == QtCore.Qt.Unchecked:
            self.emit(QtCore.SIGNAL("skipStatus(QTreeWidgetItem *)"), q_host)
            continue
         if BNMDialog.isGetRun == False:
            return
         self.emit(QtCore.SIGNAL("startProcessing(QTreeWidgetItem *)"), q_host)
         s_name = q_host.text(0).toLocal8Bit()
         s_ip = q_host.text(1).toLocal8Bit()
         s_script = BNMDialog.q_mainTree.itemWidget(q_host.child(0),1).text().toLocal8Bit()
         s_filename = BNMDialog.q_mainTree.itemWidget(q_host.child(1),1).text().toLocal8Bit()
         s_tftpdir = BNMDialog.q_mainTree.itemWidget(q_host.child(2),1).text().toLocal8Bit()
         s_time = time.strftime('%Y.%m.%d-%H-%M',time.localtime(time.time()))
         s_check = '%s/%s-%s.cfg' % (s_tftpdir, s_filename, s_time)
         s_cmd = '%s %s %s-%s.cfg' % (s_script, s_ip, s_filename, s_time)
         self.emit(QtCore.SIGNAL("showMessage(const QString &)"), QtCore.QString(s_cmd))
#         time.sleep(2)
#         s_scriptOut = 'hello'
         try:
#            c_pipe = popen2.Popen4(s_cmd)
#            c_pipe.wait()
#            s_scriptOut = c_pipe.fromchild.read()
            c_pipe = subprocess.Popen(s_cmd, shell=True, close_fds=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            c_pipe.wait()
            s_scriptOut = c_pipe.stdout.read()
         except IOError,es:
            s_scriptOut = str(es)
         self.emit(QtCore.SIGNAL("scriptOut(QTreeWidgetItem *, const QString &)"), q_host, QtCore.QString(s_scriptOut))
         if os.path.isfile(s_check) and os.stat(s_check)[ST_SIZE]:
            self.emit(QtCore.SIGNAL("okStatus(QTreeWidgetItem *)"), q_host)
         else:
            self.emit(QtCore.SIGNAL("failStatus(QTreeWidgetItem *)"), q_host)

class QStatusButton (QtGui.QPushButton):
   def __init__(self, item, parent=None):
       QtGui.QPushButton.__init__(self, parent)
       self.setUnknown()

       self.connect(self,QtCore.SIGNAL("clicked()"),self.slotStatusButton)
       self.q_item = item
   
   def setOk(self):
       self.setText(u'ok')
       self.setIcon(QtGui.QIcon(':/images/ok.png'))

   def setFail(self):
       self.setText(u'fail')
       self.setIcon(QtGui.QIcon(':/images/fail.png'))

   def setProcessing(self):
       self.setText(u'Processing...')
       self.setIcon(QtGui.QIcon(':/images/exec.png'))

   def setSkip(self):
       self.setText(u'skip...')
       self.setIcon(QtGui.QIcon(':/images/skip.png'))
       
   def setUnknown(self):
       self.setText(u'unknown...')
       self.setIcon(QtGui.QIcon(':/images/skip.png'))

   def slotStatusButton(self):
      QViewLog(self.q_item.data(2, QtCore.Qt.UserRole).toString()).exec_()
       
class QBNMTree (QtGui.QTreeWidget):
   def __init__(self, parent=None):
      QtGui.QTreeWidget.__init__(self, parent)
      
      self.setHeaderLabels([u'Param',u'Value',u'Status'])
      self.q_domDoc = QtXml.QDomDocument()
      

   def createItem(self, name, ip, script, filename, tftpdir):
      q_item = QtGui.QTreeWidgetItem()
      q_item.setFlags(q_item.flags() | QtCore.Qt.ItemIsEditable)
      q_item.setText(0,name)
      q_item.setText(1,ip)
      q_item.setIcon(0, QtGui.QIcon(':/images/host.png'))
      self.addTopLevelItem(q_item)
      
      q_statusButton = QStatusButton(q_item)
      self.setItemWidget(q_item,2,q_statusButton)

      q_param = QtGui.QTreeWidgetItem(q_item)
      q_param.setText(0,u'Script')
      q_lineEdit = QtGui.QLineEdit(self)
      self.setItemWidget(q_param,1,q_lineEdit)
      q_lineEdit.setText(script)
      
      q_param = QtGui.QTreeWidgetItem(q_item)
      q_param.setText(0,u'FileName')
      q_lineEdit = QtGui.QLineEdit(self)
      self.setItemWidget(q_param,1,q_lineEdit)
      q_lineEdit.setText(filename)
      
      q_param = QtGui.QTreeWidgetItem(q_item)
      q_param.setText(0,u'TFTP Dir')
      q_lineEdit = QtGui.QLineEdit(self)
      self.setItemWidget(q_param,1,q_lineEdit)
      q_lineEdit.setText(tftpdir)
   
      q_param = QtGui.QTreeWidgetItem(q_item)
      q_param.setText(0,u'Enable')
      q_checkBox = QtGui.QCheckBox(self)
      self.setItemWidget(q_param,1,q_checkBox)
      q_checkBox.setCheckState(QtCore.Qt.Checked)

   def syncDoc(self):
      self.q_domDoc.clear()
      q_root = self.q_domDoc.createElement('bnm')
      q_root.setAttribute(u'version',u'1.0')
      self.q_domDoc.appendChild(q_root)
      for i in xrange(0,self.topLevelItemCount()):
         q_topItem = self.topLevelItem(i)
         q_host = self.q_domDoc.createElement('host')
         q_host.setAttribute(u'name',q_topItem.text(0))
         q_host.setAttribute(u'ip',q_topItem.text(1))
         q_root.appendChild(q_host)
         
         q_param = self.q_domDoc.createElement('param')
         q_param.setAttribute(u'script',self.itemWidget(q_topItem.child(0),1).text())
         q_param.setAttribute(u'filename',self.itemWidget(q_topItem.child(1),1).text())
         q_param.setAttribute(u'tftpdir',self.itemWidget(q_topItem.child(2),1).text())
         q_host.appendChild(q_param)
         
   def load(self,filename):
      q_file = QtCore.QFile(filename)
      q_file.open(QtCore.QIODevice.ReadOnly)
      ok, errorStr, errorLine, errorColumn = self.q_domDoc.setContent(q_file, True)
      if not ok:
         QtGui.QMessageBox.information(self.window(), self.tr("BNM"), self.tr("Parse error at line %1, column %2:\n%3").arg(errorLine).arg(errorColumn).arg(errorStr))
         return False

      q_root = self.q_domDoc.documentElement()
      if q_root.tagName() != "bnm":
         QtGui.QMessageBox.information(self.window(), self.tr("BNM"), self.tr("The file is not an BNM config file."))
         return False
      elif q_root.hasAttribute("version") and q_root.attribute("version") != "1.0":
         QtGui.QMessageBox.information(self.window(), self.tr("BNM"), self.tr("The file is not an BNM version 1.0 config file."))
         return False
      
      q_file.close()
     
      self.clear()
      q_host = q_root.firstChildElement('host')
      while not q_host.isNull():
         if q_host.hasAttribute('ip') and q_host.hasAttribute('name'):
            q_param = q_host.firstChildElement('param')
            if q_param.hasAttribute('script') and q_param.hasAttribute('filename') and q_param.hasAttribute('tftpdir'):
               self.createItem(q_host.attribute('name'), q_host.attribute('ip'), q_param.attribute('script'), q_param.attribute('filename'), q_param.attribute('tftpdir'))
            else:
               QtGui.QMessageBox.information(self.window(), self.tr("BNM"), self.tr("Error <param> attribute"))
               return False
         else:
            QtGui.QMessageBox.information(self.window(), self.tr("BNM"), self.tr("Error <host> attribute"))
            return False
         q_host = q_host.nextSiblingElement('host')
      return True
    
   def save(self, filename):
      self.syncDoc()
      q_file = QtCore.QFile(filename)
      if not q_file.open(QtCore.QIODevice.ReadWrite | QtCore.QIODevice.Truncate):
         return False
      out = QtCore.QTextStream(q_file)
      self.q_domDoc.save(out, 4)
      q_file.close()
      return True

class QBNMDialog (QtGui.QDialog):
   def __init__(self, parent=None):
      QtGui.QDialog.__init__(self, parent)
      
      self.q_getRunThread = QGetRunThread()
      self.isGetRun = False
      
      q_mainLayout = QtGui.QGridLayout()
      
      self.q_mainTree = QBNMTree()
      q_mainLayout.addWidget(self.q_mainTree, 0, 0)
      
      q_buttonLayout = QtGui.QVBoxLayout()
      self.q_buttonLoad = QtGui.QPushButton(u'Load')
      q_buttonLayout.addWidget(self.q_buttonLoad)
      
      self.q_buttonSave = QtGui.QPushButton(u'Save')
      q_buttonLayout.addWidget(self.q_buttonSave)
      
      self.q_buttonAdd = QtGui.QPushButton(u'Add')
      q_buttonLayout.addWidget(self.q_buttonAdd)
      
      self.q_buttonDel = QtGui.QPushButton(u'Delete')
      q_buttonLayout.addWidget(self.q_buttonDel)
      
      q_buttonLayout.addSpacing(20)
      self.q_buttonEnableAll = QtGui.QPushButton(u'Enable All')
      q_buttonLayout.addWidget(self.q_buttonEnableAll)
      self.q_buttonDisableAll = QtGui.QPushButton(u'Disable All')
      q_buttonLayout.addWidget(self.q_buttonDisableAll)
      
      q_buttonLayout.addSpacing(20)
      self.q_buttonGetRun = QtGui.QPushButton(u'GetRun')
      q_buttonLayout.addWidget(self.q_buttonGetRun)
      
      q_buttonLayout.addStretch()
      
      q_mainLayout.addLayout(q_buttonLayout,0,1)
      
      self.q_statusBar = QtGui.QStatusBar();
      self.q_statusBar.showMessage(u'BNM Ready')
      q_mainLayout.addWidget(self.q_statusBar,1,0,1,2)
      
      self.connect(self.q_getRunThread,QtCore.SIGNAL("startProcessing(QTreeWidgetItem *)"), self.slotStartProcessing)
      self.connect(self.q_getRunThread,QtCore.SIGNAL("okStatus(QTreeWidgetItem *)"), self.slotOkStatus)
      self.connect(self.q_getRunThread,QtCore.SIGNAL("failStatus(QTreeWidgetItem *)"), self.slotFailStatus)
      self.connect(self.q_getRunThread,QtCore.SIGNAL("skipStatus(QTreeWidgetItem *)"), self.slotSkipStatus)
      self.connect(self.q_getRunThread,QtCore.SIGNAL("scriptOut(QTreeWidgetItem *, const QString &)"), self.slotScriptOut)
      self.connect(self.q_getRunThread,QtCore.SIGNAL("showMessage(const QString &)"), self.slotShowMessage)
      self.connect(self.q_getRunThread,QtCore.SIGNAL("finished()"), self.slotFinished)
      
      self.connect(self.q_buttonAdd,QtCore.SIGNAL("clicked()"),self.slotAddItem)
      self.connect(self.q_buttonDel,QtCore.SIGNAL("clicked()"),self.slotDeleteItem)
      self.connect(self.q_buttonLoad,QtCore.SIGNAL("clicked()"),self.slotLoadItems)
      self.connect(self.q_buttonSave,QtCore.SIGNAL("clicked()"),self.slotSaveItems)
      self.connect(self.q_buttonGetRun,QtCore.SIGNAL("clicked()"),self.slotGetRun)
      self.connect(self.q_buttonEnableAll,QtCore.SIGNAL("clicked()"),self.slotEnableAll)
      self.connect(self.q_buttonDisableAll,QtCore.SIGNAL("clicked()"),self.slotDisableAll)
      
      self.setLayout(q_mainLayout)
   
   def enableAll(self, enable):
      if enable:
         flag = QtCore.Qt.Checked
      else:
         flag = QtCore.Qt.Unchecked
      for i in xrange(0,self.q_mainTree.topLevelItemCount()):
         q_host = self.q_mainTree.topLevelItem(i)
         self.q_mainTree.itemWidget(q_host.child(3),1).setCheckState(flag)
   
#   def clearStatus(self):
#      for i in xrange(0,self.q_mainTree.topLevelItemCount()):
#         q_host = self.q_mainTree.topLevelItem(i)
#         q_host.setText(2, u'')
#         q_host.setIcon(2, QtGui.QIcon())

   def slotAddItem(self):
      self.q_mainTree.createItem(u'NoName', u'0.0.0.0', u'get-run.exp', u'Please enter file name', u'/tftpboot')
      self.q_statusBar.showMessage(u'Add empty item...')
   
   def slotDeleteItem(self):
      i = self.q_mainTree.indexOfTopLevelItem(self.q_mainTree.currentItem())
      if i != -1:
         self.q_mainTree.takeTopLevelItem(i)
         self.q_statusBar.showMessage(u'Delete selected item...')

   def slotLoadItems(self):
      s_file = QtGui.QFileDialog.getOpenFileName(self, u'Select BNM config file', u'', u'BNM-config (*.xml);;All Files (*)')
      if not s_file.isEmpty():
         if self.q_mainTree.load(s_file):
            self.q_statusBar.showMessage(u'BNM config file loaded successful...')
         else:
            self.q_statusBar.showMessage(u'BNM config file loading failed...')
      
   def slotSaveItems(self):
      s_file = QtGui.QFileDialog.getSaveFileName(self, u'Save BNM config', u'', u'BNM-config (*.xml);;All Files (*)')
      if not s_file.isEmpty():
         if self.q_mainTree.save(s_file):
            self.q_statusBar.showMessage(u'BNM config file saved successful...')
         else:
            self.q_statusBar.showMessage(u'BNM config file saving failed...')
      
   def slotGetRun(self): 
      if not self.isGetRun:
         self.isGetRun = True
         self.q_buttonLoad.setDisabled(True)
         self.q_buttonSave.setDisabled(True)
         self.q_buttonAdd.setDisabled(True)
         self.q_buttonDel.setDisabled(True)
         self.q_buttonEnableAll.setDisabled(True)
         self.q_buttonDisableAll.setDisabled(True)
         self.q_buttonGetRun.setText('Stop')
#         self.clearStatus()
         self.q_getRunThread.start()
         return
      if self.isGetRun:
         self.isGetRun = False
         self.q_statusBar.showMessage(u'Stopping in progress... wait...')
         return

   def slotEnableAll(self):
      self.enableAll(True)
      
   def slotDisableAll(self):
      self.enableAll(False)
   
   def slotStartProcessing(self, q_host):
      BNMDialog.q_mainTree.itemWidget(q_host,2).setProcessing()
   
   def slotOkStatus(self, q_host):
      BNMDialog.q_mainTree.itemWidget(q_host,2).setOk()
      
   def slotFailStatus(self, q_host):
      BNMDialog.q_mainTree.itemWidget(q_host,2).setFail()
   
   def slotSkipStatus(self, q_host):
      BNMDialog.q_mainTree.itemWidget(q_host,2).setSkip()
   
   def slotShowMessage(self, string):
      self.q_statusBar.showMessage(string)
      
   def slotScriptOut(self, q_host, string):
      q_host.setData(2, QtCore.Qt.UserRole,QtCore.QVariant(string))

   def slotFinished(self):
      self.isGetRun = False
      self.q_buttonLoad.setDisabled(False)
      self.q_buttonSave.setDisabled(False)
      self.q_buttonAdd.setDisabled(False)
      self.q_buttonDel.setDisabled(False)
      self.q_buttonEnableAll.setDisabled(False)
      self.q_buttonDisableAll.setDisabled(False)
      self.q_buttonGetRun.setText('GetRun')
      s_finish = u'GetRun finished at %s' % (time.strftime('%Y.%m.%d-%H-%M',time.localtime(time.time())))
      self.q_statusBar.showMessage(s_finish)
      
if __name__ == "__main__":
   appBNM = QtGui.QApplication(sys.argv)
   appBNM.setStyle('plastique')
   BNMDialog = QBNMDialog()
   
   BNMDialog.setWindowTitle(u'BNM ver 0.3')
   BNMDialog.setWindowIcon(QtGui.QIcon(':/images/exec.png'))
   sys.exit(BNMDialog.exec_())
