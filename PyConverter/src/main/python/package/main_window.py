from PySide2 import QtWidgets, QtCore, QtGui

from package.image import CustomImage


class Worker(QtCore.QObject):
    image_converted = QtCore.Signal(object, bool)
    finished = QtCore.Signal()

    def __init__(self, images_to_convert, quality, size, folder):
        super().__init__()
        self.images_to_convert = images_to_convert
        self.quality = quality
        self.size = size
        self.folder = folder
        self.runs = True

    def convert_images(self):
        for image_lw_item in self.images_to_convert:
            if self.runs and not image_lw_item.processed:
                image = CustomImage(path=image_lw_item.text(), folder=self.folder)
                success = image.reduce_image(size=self.size, quality=self.quality)
                self.image_converted.emit(image_lw_item, success)

        self.finished.emit()


class MainWindow(QtWidgets.QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle("PyConverter")
        self.setup_ui()

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layouts()
        self.add_widgets_to_layouts()
        self.setup_connections()

    def create_widgets(self):
        self.lbl_quality = QtWidgets.QLabel("Qualité:")
        self.spn_quality = QtWidgets.QSpinBox()
        self.lbl_size = QtWidgets.QLabel("Taille:")
        self.spn_size = QtWidgets.QSpinBox()
        self.lbl_dossierOut = QtWidgets.QLabel("Dossier de sortie:")
        self.le_dossierOut = QtWidgets.QLineEdit()
        self.lw_files = QtWidgets.QListWidget()
        self.btn_convert = QtWidgets.QPushButton("Conversion")
        self.lbl_dropInfo = QtWidgets.QLabel("^ Déposez les images sur l'interface")

    def modify_widgets(self):
        css_file = self.ctx.get_resource("style.css")
        with open(css_file, "r") as f:
            self.setStyleSheet(f.read())

        # Alignment
        self.spn_quality.setAlignment(QtCore.Qt.AlignRight)
        self.spn_size.setAlignment(QtCore.Qt.AlignRight)
        self.le_dossierOut.setAlignment(QtCore.Qt.AlignRight)

        # Range
        self.spn_quality.setRange(1, 100)
        self.spn_quality.setValue(75)
        self.spn_size.setRange(1, 100)
        self.spn_size.setValue(50)

        # Divers
        self.le_dossierOut.setPlaceholderText("Dossier de sortie...")
        self.le_dossierOut.setText("reduced")
        self.lbl_dropInfo.setVisible(False)

        self.setAcceptDrops(True)
        self.lw_files.setAlternatingRowColors(True)
        self.lw_files.setSelectionMode(QtWidgets.QListWidget.ExtendedSelection)

    def create_layouts(self):
        self.main_layout = QtWidgets.QGridLayout(self)

    def add_widgets_to_layouts(self):
        self.main_layout.addWidget(self.lbl_quality, 0, 0, 1, 1)
        self.main_layout.addWidget(self.spn_quality, 0, 1, 1, 1)
        self.main_layout.addWidget(self.lbl_size, 1, 0, 1, 1)
        self.main_layout.addWidget(self.spn_size, 1, 1, 1, 1)
        self.main_layout.addWidget(self.lbl_dossierOut, 2, 0, 1, 1)
        self.main_layout.addWidget(self.le_dossierOut, 2, 1, 1, 1)
        self.main_layout.addWidget(self.lw_files, 3, 0, 1, 2)
        self.main_layout.addWidget(self.lbl_dropInfo, 4, 0, 1, 2)
        self.main_layout.addWidget(self.btn_convert, 5, 0, 1, 2)

    def setup_connections(self):
        QtWidgets.QShortcut(QtGui.QKeySequence("Backspace"), self.lw_files, self.delete_selected_items)
        self.btn_convert.clicked.connect(self.convert_images)

    def convert_images(self):
        quality = self.spn_quality.value()
        size = self.spn_size.value() / 100.0
        folder = self.le_dossierOut.text()

        lw_items = [self.lw_files.item(index) for index in range(self.lw_files.count())]
        images_a_convertir = [1 for lw_item in lw_items if not lw_item.processed]
        if not images_a_convertir:
            msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                            "Aucune image à convertir",
                                            "Toutes les images ont déjà été converties.")
            msg_box.exec_()
            return False

        self.thread = QtCore.QThread(self)

        self.worker = Worker(images_to_convert=lw_items,
                             quality=quality,
                             size=size,
                             folder=folder)

        self.worker.moveToThread(self.thread)
        self.worker.image_converted.connect(self.image_converted)
        self.thread.started.connect(self.worker.convert_images)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

        self.prg_dialog = QtWidgets.QProgressDialog("Conversion des images", "Annuler...", 1, len(images_a_convertir))
        self.prg_dialog.canceled.connect(self.abort)
        self.prg_dialog.show()

    def abort(self):
        self.worker.runs = False
        self.thread.quit()

    def image_converted(self, lw_item, success):
        if success:
            lw_item.setIcon(self.ctx.img_checked)
            lw_item.processed = True
            self.prg_dialog.setValue(self.prg_dialog.value() + 1)

    def delete_selected_items(self):
        for lw_item in self.lw_files.selectedItems():
            row = self.lw_files.row(lw_item)
            self.lw_files.takeItem(row)

    def dragEnterEvent(self, event):
        self.lbl_dropInfo.setVisible(True)
        event.accept()

    def dragLeaveEvent(self, event):
        self.lbl_dropInfo.setVisible(False)

    def dropEvent(self, event):
        event.accept()
        for url in event.mimeData().urls():
            self.add_file(path=url.toLocalFile())

        self.lbl_dropInfo.setVisible(False)

    def add_file(self, path):
        items = [self.lw_files.item(index).text() for index in range(self.lw_files.count())]
        if path not in items:
            lw_item = QtWidgets.QListWidgetItem(path)
            lw_item.setIcon(self.ctx.img_unchecked)
            lw_item.processed = False
            self.lw_files.addItem(lw_item)
