# coding=UTF-8
#
# Copyright (C) 2015  Michell Stuttgart

# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.

# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/
#

from PySide import QtCore, QtSql

from comic import Comic
from compact_file_loader_factory import LoaderFactory
from page import *
from path_file_filter import PathFileFilter
from src.pynocchio_exception import NoDataFindException
from src.pynocchio_exception import InvalidTypeFileException
from src.pynocchio_exception import LoadComicsException
from utility import Utility
from settings_manager import SettingsManager
from bookmark_database_manager import BookmarkManager


class MainWindowModel(QtCore.QObject):
    _ORIGINAL_FIT = 'action_original_fit'
    _VERTICAL_FIT = 'action_vertical_fit'
    _HORIZONTAL_FIT = 'action_horizontal_fit'
    _BEST_FIT = 'action_best_fit'

    load_progress = QtCore.Signal(int)
    load_done = QtCore.Signal()

    def __init__(self):
        super(MainWindowModel, self).__init__()
        self.comic = None
        self.settings_manager = SettingsManager()
        self.rotateAngle = 0
        self.scroll_area_size = None
        self.fit_type = self.load_view_adjust(MainWindowModel._ORIGINAL_FIT)
        self.current_directory = self.load_current_directory()

        ext_list = ["*.cbr", "*.cbz", "*.rar", "*.zip", "*.tar", "*.cbt"]
        self.path_file_filter = PathFileFilter(ext_list)

    def save_recent_files(self, recent_files_list):
        self.settings_manager.save_recent_files(recent_files_list)

    def load_recent_files(self):
        return self.settings_manager.load_recent_files()

    def save_view_adjust(self, object_name):
        self.settings_manager.save_view_adjust(object_name)

    def load_view_adjust(self, default_object_name):
        return self.settings_manager.load_view_adjust(default_object_name)

    def save_current_directory(self, current_directory):
        self.settings_manager.save_current_directory(current_directory)

    def load_current_directory(self):
        return self.settings_manager.load_current_directory()

    def load(self, filename, initial_page=0):

        image_extensions = ['.bmp', '.jpg', '.jpeg', '.gif', '.png', '.pbm',
                            '.pgm', '.ppm', '.tiff', '.xbm', '.xpm', '.webp']

        ld = LoaderFactory.create_loader(
            Utility.get_file_extension(filename), set(image_extensions))

        ld.progress.connect(self.load_progressbar_value)
        # ld.progress.connect(self.load_progressbar_done)

        try:
            ld.load(filename)
        except NoDataFindException as excp:
            # Caso nao exista nenhuma imagem, carregamos a imagem indicando
            # erro
            print excp.message
            q_file = QtCore.QFile(":/icons/notCover.png")
            q_file.open(QtCore.QIODevice.ReadOnly)
            ld.data.append({
                'data': q_file.readAll(),
                'name': 'exit_red_1.png'
            })

        self.comic = Comic(Utility.get_base_name(filename),
                           Utility.get_dir_name(filename), initial_page)

        self.comic.pages = ld.data

        # for index, p in enumerate(ld.data):
        #     self.comic.add_page(Page(p['data'], p['name'], index + 1))

        self.current_directory = Utility.get_dir_name(filename)
        self.path_file_filter.parse(filename)

    def save_current_page_image(self, file_name):
        self.get_current_page().save(file_name)

    def next_page(self):
        if self.comic:
            self.comic.go_next_page()
            # self.controller.set_view_content(self.get_current_page())

    def previous_page(self):
        if self.comic:
            self.comic.go_previous_page()
            # self.controller.set_view_content(self.get_current_page())

    def first_page(self):
        if self.comic:
            self.comic.go_first_page()
            # self.controller.set_view_content(self.get_current_page())

    def last_page(self):
        if self.comic:
            self.comic.go_last_page()
            # self.controller.set_view_content(self.get_current_page())

    def next_comic(self):
        return self.path_file_filter.next_path.decode('utf-8')

    def previous_comic(self):
        return self.path_file_filter.previous_path.decode('utf-8')

    def rotate_left(self):
        self.rotateAngle = (self.rotateAngle - 90) % 360
        # self.controller.set_view_content(self.get_current_page())

    def rotate_right(self):
        self.rotateAngle = (self.rotateAngle + 90) % 360
        # self.controller.set_view_content(self.get_current_page())

    def get_comic_name(self):
        return self.comic.name if self.comic else ''

    def get_comic_title(self):
        return self.comic.name.decode('utf8') + ' - Pynocchio Comic Reader'

    def get_current_page(self):
        if self.comic:
            pix_map = self.comic.get_current_page().pixmap
            pix_map = self._rotate_page(pix_map)
            pix_map = self._resize_page(pix_map)
            return pix_map

        return None

    def get_current_page_title(self):
        return self.comic.get_current_page_title() if self.comic else ''

    def set_current_page_index(self, idx):
        if self.comic:
            self.comic.set_current_page_index(idx)

    def get_current_page_index(self):
        return self.comic.current_page_index if self.comic else -1

    def is_first_page(self):
        if self.comic and self.comic.current_page_index == 0:
            return True
        return False

    def is_last_page(self):
        if self.comic and self.comic.current_page_index + 1 == \
                self.comic.get_number_of_pages():
            return True
        return False

    def is_firts_comic(self):
        return self.path_file_filter.is_first_file()

    def is_last_comic(self):
        return self.path_file_filter.is_last_file()

    def _rotate_page(self, pix_map):
        if self.rotateAngle != 0:
            trans = QtGui.QTransform().rotate(self.rotateAngle)
            pix_map = QtGui.QPixmap(pix_map.transformed(trans))
        return pix_map

    def _resize_page(self, pix_map):

        if self.fit_type == MainWindowModel._VERTICAL_FIT:
            pix_map = pix_map.scaledToHeight(
                self.scroll_area_size.height(),
                QtCore.Qt.SmoothTransformation)

        elif self.fit_type == MainWindowModel._HORIZONTAL_FIT:
            pix_map = pix_map.scaledToWidth(
                self.scroll_area_size.width(),
                QtCore.Qt.SmoothTransformation)

        elif self.fit_type == MainWindowModel._BEST_FIT:
            pix_map = pix_map.scaledToWidth(
                self.scroll_area_size.width() * 0.8,
                QtCore.Qt.SmoothTransformation)

        return pix_map

    def original_fit(self):
        self.fit_type = MainWindowModel._ORIGINAL_FIT
        # self.controller.set_view_content(self.get_current_page())

    def vertical_fit(self):
        self.fit_type = MainWindowModel._VERTICAL_FIT
        # self.controller.set_view_content(self.get_current_page())

    def horizontal_fit(self):
        self.fit_type = MainWindowModel._HORIZONTAL_FIT
        # self.controller.set_view_content(self.get_current_page())

    def best_fit(self):
        self.fit_type = MainWindowModel._BEST_FIT
        # self.controller.set_view_content(self.get_current_page())

    @QtCore.Slot(int)
    def load_progressbar_value(self, percent):
        self.load_progress.emit(percent)

    @QtCore.Slot()
    def load_progressbar_done(self):
        self.load_done.emit()

    def save_settings(self):
        self.save_view_adjust(self.fit_type)
        self.save_current_directory(self.current_directory)
        # ld.done.connect(self.controller.view.statusbar.close_progress_bar)

    @staticmethod
    def get_bookmark_list(n):
        BookmarkManager.connect()
        bookmark_list = BookmarkManager.get_bookmarks(n)
        BookmarkManager.close()
        return bookmark_list

    @staticmethod
    def get_bookmark_from_path(path):
        BookmarkManager.connect()
        bk = BookmarkManager.get_bookmark_by_path(path)
        BookmarkManager.close()
        return bk

    def add_bookmark(self):
        db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName("file.db")
        if not db.open():
            return False
        query = QtSql.QSqlQuery()

        query.exec_("create table if not exists bookmark(id integer primary "
                    "key, path var_char, name varchar, page_number int, "
                    "page_data blob)")

        q = "INSERT INTO bookmark (id, path, name, page_number, page_data) "\
            "VALUES (:Id, :path, :name, :page_number, :page_data)"
        query.prepare(q)
        query.bindValue(":id", None)
        query.bindValue(":path", self.comic.get_path())
        query.bindValue(":name", self.comic.name)
        query.bindValue(":page_number", self.comic.get_current_page_number())
        query.bindValue(":page_data", self.comic.get_current_page().data)
        query.exec_()

        db.close()
        return True

    def remove_bookmark(self):
        if self.comic:
            BookmarkManager.connect()
            BookmarkManager.remove_bookmark(self.comic.get_path())
            BookmarkManager.close()
