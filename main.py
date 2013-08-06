#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals, division
import datetime
from itertools import product
from math import cos, sin, pi
from random import choice
import sys

import numpy as np
from numpy import array, concatenate
from OpenGL import GLU
from OpenGL.GL import *
from PIL import Image
from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4 import QtGui
from PyQt4 import QtOpenGL
from PyQt4.QtGui import (
    QPixmap, QCursor, QSlider, QGroupBox, QGridLayout, QLabel, QDockWidget)


from OpenGL.arrays import numpymodule
numpymodule.NumpyHandler.ERROR_ON_COPY = True


class TextureImage(object):
    def __init__(self, filename):
        self.img = Image.open(filename)
        self.width, self.height = self.img.size
        self.str = self.img.tostring()


class GLWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        self.parent = parent
        super(GLWidget, self).__init__(parent)
        self.x = 0.0
        self.y = 2.5
        self.z = 0.0
        self.dx = 0.0
        self.dy = 0.0
        self.dz = 0.0
        self.adx = 0.0  # degrés
        self.ady = 0.0  # degrés
        self.action = None
        self.action_amount = 1.0
        self.spot_position = None
        self.spot_direction = None
        self.fixed_spot = False
        self.frames_counted = 0
        self.fps_iterations = 0
        self.texture = TextureImage('texture.png')

    @property
    def arx(self):
        """
        Angle de l'axe x, en radians.
        """
        return self.adx * pi / 180.0

    @property
    def ary(self):
        """
        Angle de l'axe y, en radians.
        """
        return self.ady * pi / 180.0

    def initializeGL(self):
        self.qglClearColor(QtGui.QColor(0, 0, 150))

        glShadeModel(GL_FLAT)

        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        mat_specular = (0.5,) * 4
        mat_shininess = 100.0
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)
        glLightfv(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.00005)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.7,) * 4)

        glEnable(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D,
                     0, GL_RGB, self.texture.width, self.texture.height,
                     0, GL_RGB, GL_UNSIGNED_BYTE, self.texture.str)

        self.initGeometry()

        self.last_time = datetime.datetime.now()
        self.current_time = datetime.datetime.now()

    def resizeGL(self, width, height):
        if height == 0:
            height = 1

        glViewport(0, 0, width, height)
        self.parent.width = width
        self.parent.height = height

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        spot_direction = (
            -sin(self.ary) * cos(self.arx),
            sin(self.arx),
            -cos(self.ary) * cos(self.arx),
        )

        if self.fixed_spot:
            if self.spot_direction is None:
                self.spot_direction = spot_direction
            spot_direction = self.spot_direction

        spot_position = (-self.x, self.y, -self.z)
        if self.fixed_spot:
            if self.spot_position is None:
                self.spot_position = spot_position
            spot_position = self.spot_position
        glLightiv(GL_LIGHT0, GL_SPOT_CUTOFF, self.parent.spot_slider.value())
        glTranslate(*spot_position)

        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, spot_direction)
        glLightfv(GL_LIGHT0, GL_POSITION, (0.0, 0.0, 0.0) + (1.0,))

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.parent.width / float(self.parent.height)

        GLU.gluPerspective(
            self.parent.fov_slider.value(), aspect, 1.0, 100000.0)

        glRotate(self.adx, -1.0, 0.0, 0.0)
        glRotate(self.ady, 0.0, -1.0, 0.0)
        glTranslate(self.x, -self.y, self.z)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointerf(self.vertices)

        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glTexCoordPointeri(self.texcoords)

        glDrawElementsui(GL_QUADS, self.indices)

    def initGeometry(self):
        start = datetime.datetime.now()
        print('Création du monde…')

        n = 300

        vertices = array([
            [0, 0, 0],  # Front bottom right
            [1, 0, 0],  # Front bottom left
            [1, 1, 0],  # Front top    right
            [0, 1, 0],  # Front top    left
            [0, 0, 1],  # Back  bottom right
            [1, 0, 1],  # Back  bottom left
            [1, 1, 1],  # Back  top    left
            [0, 1, 1],  # Back  top    right
        ])
        self.vertices = concatenate(
            [vertices + (x, 0, z)
             for x, z in product(range(-n // 2, n // 2), repeat=2)]
        ).astype(b'float32', copy=False)
        print('Chargement des points terminé.')

        # Modèle de cube avec de GL_QUADS.
        self.indices = concatenate([array([
            0, 1, 2, 3,  # Front  face
            7, 6, 5, 4,  # Back   face
            3, 2, 6, 7,  # Top    face
            0, 3, 7, 4,  # Bottom face
            2, 1, 5, 6,  # Left   face
            1, 0, 4, 5,  # Right  face
        ]) + 8 * x for x in range(n ** 2)]).astype(b'uint32', copy=False)
        # Modèle de cube avec des GL_TRIANGLES.
        # self.indices = concatenate([array([
        #     0, 1, 2,
        #     2, 3, 0,
        #     3, 2, 6,
        #     6, 7, 3,
        #     3, 7, 4,
        #     4, 0, 3,
        #     0, 4, 1,
        #     1, 4, 5,
        #     1, 6, 2,
        #     1, 5, 6,
        #     5, 7, 6,
        #     7, 5, 4,
        # ]) + 8 * x for x in range(n ** 2)]).astype(b'uint32', copy=False)
        print('Chargement des polygones terminé.')

        self.texcoords = np.tile(
            array([[0, 0], [1, 0], [1, 1], [0, 1],
                   [1, 0], [2, 0], [2, 1], [1, 1]]),
            (len(self.vertices) / 8, 1)).astype('int32')
        print('Chargement des textures terminé.')

        print('Chargement du monde effectué en %s secondes'
              % (datetime.datetime.now() - start).total_seconds())

    def updateGeometry(self):
        if self.action:
            cubes_len = len(self.vertices) / 8.0
            for i in np.random.randint(cubes_len, size=250) * 8:
                self.vertices[i:i + 8] += (0, self.action, 0)

    def updateDispatcher(self):
        self.updatePosition()
        self.updateStatusBar()
        self.updateGL()
        self.fps_iterations += 1

    def updatePosition(self):
        self.adx %= 360.0
        self.ady %= 360.0
        a = self.ary
        a_side = a + pi/2
        self.x += self.dz * sin(a) + self.dx * sin(a_side)
        self.y += self.dy
        self.z += self.dz * cos(a) + self.dx * cos(a_side)

    def updateStatusBar(self):
        seconds_elapsed = (self.current_time - self.last_time).total_seconds()
        self.parent.statusBar().showMessage(
            'fps: %s x: %s  y: %s  z: %s  rotx: %s  roty: %s polygones: %s' % (
                self.frames_counted / seconds_elapsed,
                self.x, self.y, self.z,
                self.adx, self.ady,
                len(self.indices) / 4))  # 4 points par face.

    def updateFPS(self):
        self.last_time = self.current_time
        self.current_time = datetime.datetime.now()
        self.frames_counted = self.fps_iterations
        self.fps_iterations = 0


class Window(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.width = 1366
        self.height = 768
        self.resize(self.width, self.height)
        self.setWindowTitle('Expérience OpenGL')

        self.glWidget = GLWidget(self)
        self.setCentralWidget(self.glWidget)

        self.initActions()
        self.initMenus()

        self.mouse_x = None
        self.mouse_y = None
        self.mouse_locked = False

        timer = QtCore.QTimer(self)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'),
                               self.glWidget.updateDispatcher)
        timer.start(1000.0 / 60.0)

        geometry_timer = QtCore.QTimer(self)
        QtCore.QObject.connect(geometry_timer, QtCore.SIGNAL('timeout()'),
                               self.glWidget.updateGeometry)
        geometry_timer.start(1000.0 / 60.0)

        fps_timer = QtCore.QTimer(self)
        QtCore.QObject.connect(fps_timer, QtCore.SIGNAL('timeout()'),
                               self.glWidget.updateFPS)
        fps_timer.start(1000.0)

    def lockMouse(self):
        self.mouse_locked = True
        self.setMouseTracking(True)
        self.setFocus()

        px = QPixmap(32, 32)
        px.fill()
        px.setMask(px.createHeuristicMask())

        self.setCursor(QCursor(px))
        self.grabMouse(self.cursor())

    def unlockMouse(self):
        self.releaseMouse()
        self.setMouseTracking(False)
        self.setCursor(Qt.ArrowCursor)

        self.mouse_x = None
        self.mouse_y = None
        self.mouse_locked = False

    def initActions(self):
        self.fullscreenAction = QtGui.QAction('Full&screen', self)
        self.fullscreenAction.setShortcut('F11')
        self.exitAction = QtGui.QAction('&Quit', self)

        def full():
            self.unlockMouse()
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            self.lockMouse()

        self.connect(self.fullscreenAction, QtCore.SIGNAL('triggered()'), full)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.connect(self.exitAction, QtCore.SIGNAL('triggered()'), self.close)

    def initMenus(self):
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self.fullscreenAction)
        fileMenu.addAction(self.exitAction)

        self.controls = QGroupBox()
        controls_layout = QGridLayout()

        self.text = QtGui.QTextEdit("""
        <b>ZQSD</b> : Déplacement<br/>
        <b>Espace</b> : Monter<br/>
        <b>Maj</b> : Descendre<br/><br/>

        <b>Clic gauche</b> : Déplacer des cubes par centaines<br/>
        <b>Clic droit</b> : Les déplacer dans l’autre sens<br/>
        <b>Molette</b> : Changer la vitesse de déplacement des cubes<br/><br/>

        <b>Échap</b> : Relâcher la souris
        """)
        self.text.setReadOnly(True)
        self.text.setMaximumHeight(280)
        controls_layout.addWidget(self.text, 0, 0)

        controls_layout.addWidget(QLabel('Champ de vision'), 1, 0)
        self.fov_slider = QSlider(Qt.Horizontal)
        self.fov_slider.setRange(30, 90)
        self.fov_slider.setValue(45)
        controls_layout.addWidget(self.fov_slider, 1, 1)

        controls_layout.addWidget(QLabel('Vitesse'), 2, 0)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(2)
        controls_layout.addWidget(self.speed_slider, 2, 1)

        controls_layout.addWidget(QLabel('Spot'), 3, 0)
        self.spot_slider = QSlider(Qt.Horizontal)
        self.spot_slider.setRange(1, 90)
        self.spot_slider.setValue(15)
        controls_layout.addWidget(self.spot_slider, 3, 1)

        self.controls.setLayout(controls_layout)
        dock = QDockWidget('Contrôles')
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        dock.setWidget(self.controls)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.isAutoRepeat():
            return
        key = QKeyEvent.key()
        move_amount = self.speed_slider.value()
        gl = self.glWidget
        if key == Qt.Key_Z:
            gl.dz += move_amount
        if key == Qt.Key_S:
            gl.dz -= move_amount
        if key == Qt.Key_Q:
            gl.dx += move_amount
        if key == Qt.Key_D:
            gl.dx -= move_amount
        if key == Qt.Key_Space:
            gl.dy += move_amount
        if key == Qt.Key_Shift:
            gl.dy -= move_amount
        if key == Qt.Key_Escape:
            self.unlockMouse()

    def keyReleaseEvent(self, QKeyEvent):
        if QKeyEvent.isAutoRepeat():
            return
        key = QKeyEvent.key()
        move_amount = self.speed_slider.value()
        gl = self.glWidget
        if key == Qt.Key_Z:
            gl.dz -= move_amount
        if key == Qt.Key_S:
            gl.dz += move_amount
        if key == Qt.Key_Q:
            gl.dx -= move_amount
        if key == Qt.Key_D:
            gl.dx += move_amount
        if key == Qt.Key_Space:
            gl.dy -= move_amount
        if key == Qt.Key_Shift:
            gl.dy += move_amount

    def mouseMoveEvent(self, QMouseEvent):
        mouse_x = QMouseEvent.x()
        mouse_y = QMouseEvent.y()

        if self.mouse_x is None and self.mouse_y is None:
            p = self.mapToGlobal(QMouseEvent.pos())
            self.global_mouse_x, self.global_mouse_y = p.x(), p.y()
            self.mouse_x = mouse_x
            self.mouse_y = mouse_y

        if self.mouse_locked:
            self.cursor().setPos(self.global_mouse_x, self.global_mouse_y)

        self.glWidget.ady -= (mouse_x - self.mouse_x) / 10.0
        self.glWidget.adx -= (mouse_y - self.mouse_y) / 10.0

    def wheelEvent(self, QWheelEvent):
        self.glWidget.action_amount += QWheelEvent.delta() / 120.0
        self.mousePressEvent(QWheelEvent)

    def mousePressEvent(self, QMouseEvent):
        if not self.mouse_locked:
            self.lockMouse()
            return
        button = QMouseEvent.buttons()
        action = 0
        action_amount = self.glWidget.action_amount
        if button == Qt.LeftButton:
            action += action_amount
        if button == Qt.RightButton:
            action -= action_amount
        if button == Qt.MiddleButton:
            self.glWidget.fixed_spot = not self.glWidget.fixed_spot
            if not self.glWidget.fixed_spot:
                self.glWidget.spot_position = None
                self.glWidget.spot_direction = None
        self.glWidget.action = action or None

    def mouseReleaseEvent(self, QMouseEvent):
        self.glWidget.action = None

    def close(self):
        QtGui.qApp.quit()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    win = Window()
    win.show()

    sys.exit(app.exec_())
