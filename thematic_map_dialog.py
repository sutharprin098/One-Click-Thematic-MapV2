from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QProgressDialog, QColorDialog, QFileDialog
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsSymbol, 
    QgsRendererRange, QgsGraduatedSymbolRenderer,
    QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol,
    QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling, Qgis
)
from qgis.PyQt.QtCore import Qt, QCoreApplication
import os.path
import json
import traceback
import numpy as np

from .thematic_map_dialog_ui import Ui_ThematicMapDialog


class ThematicMapDialog(QDialog, Ui_ThematicMapDialog):
    def __init__(self, iface):
        QDialog.__init__(self)
        self.setupUi(self)
        self.iface = iface
        self.previous_renderers = {}
        self.custom_min_color = QColor(173, 216, 230)  # Light blue
        self.custom_max_color = QColor(8, 81, 156)     # Dark blue
        self.border_color = QColor(50, 50, 50)         # Dark gray
        self.plugin_dir = os.path.dirname(__file__)
        self.styles_dir = os.path.join(self.plugin_dir, 'saved_styles')
        
        # Label styling colors
        self.label_font_color = QColor(0, 0, 0)        # Black
        self.label_bg_color = QColor(255, 255, 255)    # White
        
        # Create styles directory if it doesn't exist
        if not os.path.exists(self.styles_dir):
            os.makedirs(self.styles_dir)
        
        # Connect signals
        self.layerCombo.currentIndexChanged.connect(self.updateFieldCombo)
        self.buttonBox.accepted.connect(self.generateThematicMap)
        self.buttonBox.rejected.connect(self.close)
        
        # Color customization signals
        self.minColorButton.clicked.connect(self.chooseMinColor)
        self.maxColorButton.clicked.connect(self.chooseMaxColor)
        self.borderColorButton.clicked.connect(self.chooseBorderColor)
        self.fontColorButton.clicked.connect(self.chooseFontColor)
        self.bgColorButton.clicked.connect(self.chooseBgColor)
        self.reverseColorCheckBox.stateChanged.connect(self.updateColorDisplay)
        
        # Export/Save signals
        self.saveStyleButton.clicked.connect(self.saveCurrentStyle)
        self.loadStyleButton.clicked.connect(self.loadSavedStyle)
        self.exportQMLButton.clicked.connect(self.exportAsQML)
        
        # Statistics and Legend signals
        self.generateLegendButton.clicked.connect(self.generateLegendOnMap)
        self.labelFieldCombo.currentIndexChanged.connect(self.updateStatistics)
        self.fieldCombo.currentIndexChanged.connect(self.updateStatistics)
        
        # Opacity slider
        self.opacitySlider.valueChanged.connect(self.updateOpacityLabel)
        
        # Populate ONLY layers with numeric fields
        self.populateLayersWithNumericFields()
        
    def updateOpacityLabel(self):
        """Update opacity label when slider changes"""
        value = self.opacitySlider.value()
        self.opacityLabel.setText(f"{value}%")
        
    def chooseMinColor(self):
        """Open color picker for minimum color"""
        color = QColorDialog.getColor(self.custom_min_color, self, "Select Minimum Color")
        if color.isValid():
            self.custom_min_color = color
            self.minColorButton.setStyleSheet(f"background-color: {color.name()};")
            self.updateColorDisplay()
    
    def chooseMaxColor(self):
        """Open color picker for maximum color"""
        color = QColorDialog.getColor(self.custom_max_color, self, "Select Maximum Color")
        if color.isValid():
            self.custom_max_color = color
            self.maxColorButton.setStyleSheet(f"background-color: {color.name()};")
            self.updateColorDisplay()
    
    def chooseBorderColor(self):
        """Open color picker for border color"""
        color = QColorDialog.getColor(self.border_color, self, "Select Border Color")
        if color.isValid():
            self.border_color = color
            self.borderColorButton.setStyleSheet(f"background-color: {color.name()};")
    
    def chooseFontColor(self):
        """Open color picker for label font color"""
        color = QColorDialog.getColor(self.label_font_color, self, "Select Font Color")
        if color.isValid():
            self.label_font_color = color
            self.fontColorButton.setStyleSheet(f"background-color: {color.name()};")
    
    def chooseBgColor(self):
        """Open color picker for label background color"""
        color = QColorDialog.getColor(self.label_bg_color, self, "Select Background Color")
        if color.isValid():
            self.label_bg_color = color
            self.bgColorButton.setStyleSheet(f"background-color: {color.name()};")
    
    def updateColorDisplay(self):
        """Update color display when reverse is toggled"""
        if self.reverseColorCheckBox.isChecked():
            self.minColorButton.setStyleSheet(f"background-color: {self.custom_max_color.name()};")
            self.maxColorButton.setStyleSheet(f"background-color: {self.custom_min_color.name()};")
        else:
            self.minColorButton.setStyleSheet(f"background-color: {self.custom_min_color.name()};")
            self.maxColorButton.setStyleSheet(f"background-color: {self.custom_max_color.name()};")
    
    def saveCurrentStyle(self):
        """Save current style settings to file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Thematic Map Style",
                self.styles_dir,
                "JSON Files (*.json)"
            )
            
            if not filename:
                return
            
            style_data = {
                'classification_method': self.classMethodCombo.currentText(),
                'num_classes': self.classSpinBox.value(),
                'color_scheme': self.colorCombo.currentText(),
                'reverse_colors': self.reverseColorCheckBox.isChecked(),
                'min_color': self.custom_min_color.name(),
                'max_color': self.custom_max_color.name(),
                'border_color': self.border_color.name(),
                'border_width': self.borderWidthSpinBox.value(),
                'opacity': self.opacitySlider.value(),
                'show_labels': self.labelCheckBox.isChecked(),
                'label_field': self.labelFieldCombo.currentText(),
                'font_size': self.fontSizeSpinBox.value(),
                'font_color': self.label_font_color.name(),
                'bg_color': self.label_bg_color.name(),
                'bg_enabled': self.bgEnabledCheckBox.isChecked()
            }
            
            with open(filename, 'w') as f:
                json.dump(style_data, f, indent=2)
            
            self.iface.messageBar().pushSuccess("Success", f"Style saved: {os.path.basename(filename)}")
        except Exception as e:
            self.iface.messageBar().pushCritical("Error", f"Failed to save style: {str(e)}")
    
    def loadSavedStyle(self):
        """Load style from saved file"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Load Thematic Map Style",
                self.styles_dir,
                "JSON Files (*.json)"
            )
            
            if not filename:
                return
            
            with open(filename, 'r') as f:
                style_data = json.load(f)
            
            # Apply settings
            idx = self.classMethodCombo.findText(style_data.get('classification_method', 'Quantiles'))
            if idx >= 0:
                self.classMethodCombo.setCurrentIndex(idx)
            
            self.classSpinBox.setValue(style_data.get('num_classes', 5))
            
            idx = self.colorCombo.findText(style_data.get('color_scheme', 'Blue'))
            if idx >= 0:
                self.colorCombo.setCurrentIndex(idx)
            
            self.reverseColorCheckBox.setChecked(style_data.get('reverse_colors', False))
            self.custom_min_color = QColor(style_data.get('min_color', '#ADD8E6'))
            self.custom_max_color = QColor(style_data.get('max_color', '#0851CC'))
            self.border_color = QColor(style_data.get('border_color', '#323232'))
            self.borderWidthSpinBox.setValue(style_data.get('border_width', 0.2))
            self.opacitySlider.setValue(style_data.get('opacity', 100))
            self.labelCheckBox.setChecked(style_data.get('show_labels', True))
            
            # Load label styling
            self.label_font_color = QColor(style_data.get('font_color', '#000000'))
            self.label_bg_color = QColor(style_data.get('bg_color', '#FFFFFF'))
            self.bgEnabledCheckBox.setChecked(style_data.get('bg_enabled', True))
            self.fontColorButton.setStyleSheet(f"background-color: {self.label_font_color.name()};")
            self.bgColorButton.setStyleSheet(f"background-color: {self.label_bg_color.name()};")
            
            self.updateColorDisplay()
            self.iface.messageBar().pushSuccess("Success", f"Style loaded: {os.path.basename(filename)}")
        except Exception as e:
            self.iface.messageBar().pushCritical("Error", f"Failed to load style: {str(e)}")
    
    def exportAsQML(self):
        """Export layer style as QML"""
        try:
            layer_idx = self.layerCombo.currentIndex()
            if layer_idx <= 0 or self.layerCombo.itemData(layer_idx) is None:
                self.iface.messageBar().pushWarning("Warning", "Please select a valid layer!")
                return
            
            layer = self.layerCombo.itemData(layer_idx)
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Style as QML",
                self.styles_dir,
                "QML Files (*.qml)"
            )
            
            if not filename:
                return
            
            # Save the current renderer as QML
            if layer.renderer():
                layer.renderer().saveToFile(filename)
                self.iface.messageBar().pushSuccess("Success", f"Style exported: {os.path.basename(filename)}")
            else:
                self.iface.messageBar().pushWarning("Warning", "No renderer to export!")
        except Exception as e:
            self.iface.messageBar().pushCritical("Error", f"Failed to export QML: {str(e)}")
    
    def updateStatistics(self):
        """Update statistics display"""
        try:
            layer_idx = self.layerCombo.currentIndex()
            if layer_idx <= 0 or self.layerCombo.itemData(layer_idx) is None:
                self.statsTextEdit.setText("Select a layer first")
                return
            
            layer = self.layerCombo.itemData(layer_idx)
            field_name = self.fieldCombo.currentText()
            
            if not field_name or field_name == "No numeric fields available":
                self.statsTextEdit.setText("Select a numeric field first")
                return
            
            # Collect values
            values = []
            for feature in layer.getFeatures():
                value = feature[field_name]
                if value is not None and value != "":
                    try:
                        float_val = float(value)
                        if not (float_val == float('inf') or float_val == float('-inf')):
                            values.append(float_val)
                    except (ValueError, TypeError):
                        pass
            
            if not values:
                self.statsTextEdit.setText("No valid numeric data found")
                return
            
            # Calculate statistics
            min_val = min(values)
            max_val = max(values)
            mean_val = np.mean(values)
            median_val = np.median(values)
            std_val = np.std(values)
            count = len(values)
            
            # Display statistics
            stats_text = f"""📊 Statistics for '{field_name}':
            
• Count: {count} features
• Min: {min_val:.2f}
• Max: {max_val:.2f}
• Mean: {mean_val:.2f}
• Median: {median_val:.2f}
• Std Dev: {std_val:.2f}
• Range: {max_val - min_val:.2f}"""
            
            self.statsTextEdit.setText(stats_text)
        except Exception as e:
            self.statsTextEdit.setText(f"Error: {str(e)}")
    
    def generateLegendOnMap(self):
        """Generate legend on map canvas"""
        try:
            layer_idx = self.layerCombo.currentIndex()
            if layer_idx <= 0 or self.layerCombo.itemData(layer_idx) is None:
                self.iface.messageBar().pushWarning("Warning", "Please select a valid layer!")
                return
            
            layer = self.layerCombo.itemData(layer_idx)
            
            # Check if layer has a graduated renderer
            if not layer.renderer() or not isinstance(layer.renderer(), QgsGraduatedSymbolRenderer):
                self.iface.messageBar().pushWarning("Warning", "Apply thematic map first, then generate legend!")
                return
            
            # Open print layout manager
            layout_manager = QgsProject.instance().layoutManager()
            
            # Create a new print layout if none exists
            layouts = layout_manager.layouts()
            if not layouts:
                from qgis.core import QgsPrintLayout
                layout = QgsPrintLayout(QgsProject.instance())
                layout.initializeDefaults()
                layout.setName("Thematic Map Layout")
                layout_manager.addLayout(layout)
            else:
                layout = layouts[0]
            
            # Add legend to the layout
            from qgis.core import QgsLayoutItemLegend, QgsLayoutPoint, QgsLayoutSize
            from qgis.core import QgsUnitTypes
            
            legend = QgsLayoutItemLegend(layout)
            
            # Set legend position and size
            legend.attemptMove(QgsLayoutPoint(10, 10, QgsUnitTypes.LayoutMillimeters))
            legend.attemptResize(QgsLayoutSize(100, 150, QgsUnitTypes.LayoutMillimeters))
            
            # Update legend to show current layers
            legend.setAutoUpdateModel(False)
            
            # Get the legend model
            root = QgsProject.instance().layerTreeRoot()
            legend.model().setRootGroup(root)
            
            # Filter to show only selected layer
            legend.setLinkedMap(None)
            
            layout.addLayoutItem(legend)
            
            # Open the layout designer
            self.iface.openLayoutDesigner(layout)
            
            self.iface.messageBar().pushSuccess("Success", "Legend added to print layout! Adjust position and size as needed.")
        except Exception as e:
            error_msg = f"Failed to generate legend: {str(e)}\n\nTip: You can manually add legend from Print Layout."
            self.iface.messageBar().pushCritical("Error", error_msg)
            print(traceback.format_exc())
        
    def classify_equal_intervals(self, values, num_classes):
        """Equal intervals classification"""
        min_val = min(values)
        max_val = max(values)
        interval = (max_val - min_val) / num_classes
        
        breaks = [min_val + i * interval for i in range(num_classes + 1)]
        return breaks
    
    def classify_quantiles(self, values, num_classes):
        """Quantiles classification"""
        breaks = [np.percentile(values, (i / num_classes) * 100) for i in range(num_classes + 1)]
        return sorted(list(set(breaks)))  # Remove duplicates and sort
    
    def classify_natural_breaks(self, values, num_classes):
        """Natural breaks (Jenks) - simplified version"""
        try:
            import jenkspy
            breaks = jenkspy.jenks_breaks(values, n_classes=num_classes)
            return breaks
        except ImportError:
            # Fallback to quantiles if jenkspy not available
            return self.classify_quantiles(values, num_classes)
    
    def classify_pretty_breaks(self, values, num_classes):
        """Pretty breaks classification"""
        min_val = min(values)
        max_val = max(values)
        
        # Calculate nice round numbers
        range_val = max_val - min_val
        unit = 10 ** (len(str(int(range_val))) - 1)
        
        pretty_min = (int(min_val / unit)) * unit
        pretty_max = (int(max_val / unit) + 1) * unit
        
        interval = (pretty_max - pretty_min) / num_classes
        breaks = [pretty_min + i * interval for i in range(num_classes + 1)]
        return breaks
    
    def classify_standard_deviation(self, values, num_classes):
        """Standard deviation classification"""
        mean = np.mean(values)
        std = np.std(values)
        
        breaks = [mean + (i - num_classes/2) * std for i in range(num_classes + 1)]
        breaks = sorted(breaks)
        return breaks
        
    def has_numeric_fields(self, layer):
        """Check if layer has any numeric fields"""
        if not isinstance(layer, QgsVectorLayer):
            return False
            
        if layer.geometryType() not in [0, 1, 2]:  # Not point, line, or polygon
            return False
            
        for field in layer.fields():
            if field.type() in [2, 4, 6, 10]:  # Integer, Double, Int64, Real
                return True
        return False
    
    def get_numeric_fields(self, layer):
        """Get list of numeric field names from layer"""
        numeric_fields = []
        for field in layer.fields():
            if field.type() in [2, 4, 6, 10]:  # Integer, Double, Int64, Real
                numeric_fields.append(field.name())
        return numeric_fields
    
    def populateLayersWithNumericFields(self):
        """Populate layer dropdown ONLY with layers having numeric fields"""
        self.layerCombo.clear()
        self.layerCombo.addItem("-- Select Layer --", None)
        
        layers = QgsProject.instance().mapLayers().values()
        valid_layers = []
        
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
                if self.has_numeric_fields(layer):
                    valid_layers.append(layer)
        
        if not valid_layers:
            self.layerCombo.addItem("No layers with numeric fields found", None)
            self.layerCombo.setEnabled(False)
            self.iface.messageBar().pushWarning(
                "No Valid Layers", 
                "No vector layers with numeric fields found!\n"
                "Please load a layer with numeric attributes."
            )
        else:
            for layer in valid_layers:
                num_fields = len(self.get_numeric_fields(layer))
                self.layerCombo.addItem(
                    f"{layer.name()} ({num_fields} numeric fields, {layer.featureCount()} features)", 
                    layer
                )
    
    def updateFieldCombo(self):
        """Update field dropdown with numeric fields from selected layer"""
        self.fieldCombo.clear()
        self.labelFieldCombo.clear()
        
        index = self.layerCombo.currentIndex()
        if index <= 0:  # First item is placeholder or error
            return
            
        layer = self.layerCombo.itemData(index)
        
        if layer and self.has_numeric_fields(layer):
            numeric_fields = self.get_numeric_fields(layer)
            self.fieldCombo.addItems(numeric_fields)
            self.fieldCombo.setEnabled(True)
            
            # Add all fields (numeric and text) for label field
            all_fields = [field.name() for field in layer.fields()]
            self.labelFieldCombo.addItems(all_fields)
            if numeric_fields:
                # Default to first numeric field
                self.labelFieldCombo.setCurrentText(numeric_fields[0])
        else:
            self.fieldCombo.addItem("No numeric fields available")
            self.fieldCombo.setEnabled(False)
    
    def get_color_scheme(self, scheme_name, num_classes):
        """Return color scheme based on selection"""
        schemes = {
            'Blue': [
                QColor(247, 251, 255),
                QColor(222, 235, 247),
                QColor(198, 219, 239),
                QColor(158, 202, 225),
                QColor(107, 174, 214),
                QColor(66, 146, 198),
                QColor(33, 113, 181),
                QColor(8, 81, 156),
                QColor(8, 48, 107)
            ],
            'Red': [
                QColor(255, 245, 240),
                QColor(254, 224, 210),
                QColor(252, 187, 161),
                QColor(252, 146, 114),
                QColor(251, 106, 74),
                QColor(239, 59, 44),
                QColor(203, 24, 29),
                QColor(165, 15, 21),
                QColor(103, 0, 13)
            ],
            'Green': [
                QColor(247, 252, 245),
                QColor(229, 245, 224),
                QColor(199, 233, 192),
                QColor(161, 217, 155),
                QColor(116, 196, 118),
                QColor(65, 171, 93),
                QColor(35, 139, 69),
                QColor(0, 109, 44),
                QColor(0, 68, 27)
            ],
            'Rainbow': [
                QColor(158, 202, 225),
                QColor(171, 221, 164),
                QColor(255, 255, 191),
                QColor(253, 174, 97),
                QColor(244, 109, 67),
                QColor(215, 48, 39),
                QColor(165, 0, 38)
            ],
            'Purple': [
                QColor(252, 251, 253),
                QColor(239, 237, 245),
                QColor(218, 218, 235),
                QColor(188, 189, 220),
                QColor(158, 154, 200),
                QColor(128, 125, 186),
                QColor(106, 81, 163),
                QColor(84, 39, 143),
                QColor(63, 0, 125)
            ],
            'Heat': [
                QColor(255, 255, 204),
                QColor(255, 237, 160),
                QColor(254, 217, 118),
                QColor(254, 178, 76),
                QColor(253, 141, 60),
                QColor(252, 78, 42),
                QColor(227, 26, 28),
                QColor(189, 0, 38),
                QColor(128, 0, 38)
            ],
            'Orange': [
                QColor(255, 245, 235),
                QColor(254, 230, 206),
                QColor(253, 208, 162),
                QColor(253, 174, 107),
                QColor(254, 143, 66),
                QColor(253, 109, 30),
                QColor(236, 82, 11),
                QColor(204, 76, 2),
                QColor(140, 45, 4)
            ]
        }
        
        if scheme_name == 'Custom':
            # Use custom colors
            base_colors = [self.custom_min_color, self.custom_max_color]
        else:
            base_colors = schemes.get(scheme_name, schemes['Blue'])
        
        if self.reverseColorCheckBox.isChecked():
            base_colors = base_colors[::-1]
        
        if num_classes <= len(base_colors):
            return base_colors[:num_classes]
        else:
            colors = []
            for i in range(num_classes):
                pos = i / (num_classes - 1) if num_classes > 1 else 0
                base_idx = pos * (len(base_colors) - 1)
                idx1 = int(base_idx)
                idx2 = min(idx1 + 1, len(base_colors) - 1)
                
                if idx1 == idx2:
                    colors.append(base_colors[idx1])
                else:
                    ratio = base_idx - idx1
                    c1 = base_colors[idx1]
                    c2 = base_colors[idx2]
                    
                    r = int(c1.red() + (c2.red() - c1.red()) * ratio)
                    g = int(c1.green() + (c2.green() - c1.green()) * ratio)
                    b = int(c1.blue() + (c2.blue() - c1.blue()) * ratio)
                    
                    colors.append(QColor(r, g, b))
            return colors
    
    def generateThematicMap(self):
        """Generate thematic map with selected classification method"""
        try:
            # Get selected layer
            layer_idx = self.layerCombo.currentIndex()
            if layer_idx <= 0 or self.layerCombo.itemData(layer_idx) is None:
                self.iface.messageBar().pushWarning("Warning", "Please select a valid layer!")
                return
                
            layer = self.layerCombo.itemData(layer_idx)
            field_name = self.fieldCombo.currentText()
            
            if not field_name or field_name == "No numeric fields available":
                self.iface.messageBar().pushWarning("Warning", "Please select a numeric field!")
                return
            
            # Store previous renderer
            if layer.id() not in self.previous_renderers:
                self.previous_renderers[layer.id()] = layer.renderer().clone() if layer.renderer() else None
            
            # Get parameters
            num_classes = self.classSpinBox.value()
            color_scheme = self.colorCombo.currentText()
            classification_method = self.classMethodCombo.currentText()
            opacity = self.opacitySlider.value() / 100.0
            
            # Show progress
            progress = QProgressDialog("Processing...", "Cancel", 0, 100, self)
            progress.setWindowTitle("Creating Thematic Map")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Step 1: Collect ONLY VALID numeric data
            progress.setLabelText("Step 1/3: Reading valid features...")
            QCoreApplication.processEvents()
            
            valid_features = []  # (feature_id, value)
            null_features = []   # feature_ids with NULL/invalid values
            total_features = layer.featureCount()
            
            # Read all features - collect only valid numeric values
            for i, feature in enumerate(layer.getFeatures()):
                if progress.wasCanceled():
                    progress.close()
                    return
                    
                value = feature[field_name]
                is_valid = False
                
                # Strict validation for numeric values
                if value is not None and value != "":
                    try:
                        float_val = float(value)
                        if not (float_val == float('inf') or float_val == float('-inf')):
                            valid_features.append((feature.id(), float_val))
                            is_valid = True
                    except (ValueError, TypeError):
                        pass
                
                if not is_valid:
                    null_features.append(feature.id())
                
                # Update progress
                if i % 100 == 0:
                    progress.setValue(int((i / total_features) * 33))
                    QCoreApplication.processEvents()
            
            progress.setValue(33)
            
            # Step 2: Check if we have enough valid data
            progress.setLabelText("Step 2/3: Analyzing data...")
            QCoreApplication.processEvents()
            
            valid_count = len(valid_features)
            
            if valid_count == 0:
                progress.close()
                self.iface.messageBar().pushWarning(
                    "No Valid Data", 
                    f"No valid numeric data found in field '{field_name}'!\n"
                    f"All {total_features} features have NULL or non-numeric values."
                )
                return
            
            # Adjust number of classes based on valid data
            if valid_count < num_classes:
                num_classes = max(2, valid_count)
                self.classSpinBox.setValue(num_classes)
                self.iface.messageBar().pushInfo(
                    "Adjusted Classes", 
                    f"Reduced to {num_classes} classes (only {valid_count} valid values)"
                )
            
            # Get just the values
            values = [val for _, val in valid_features]
            values.sort()
            
            # Step 3: Create classification
            progress.setLabelText("Step 3/3: Creating classification...")
            QCoreApplication.processEvents()
            
            # Apply classification method
            if classification_method == 'Equal Intervals':
                breaks = self.classify_equal_intervals(values, num_classes)
            elif classification_method == 'Natural Breaks (Jenks)':
                breaks = self.classify_natural_breaks(values, num_classes)
            elif classification_method == 'Pretty Breaks':
                breaks = self.classify_pretty_breaks(values, num_classes)
            elif classification_method == 'Standard Deviation':
                breaks = self.classify_standard_deviation(values, num_classes)
            else:  # Default: Quantiles
                breaks = self.classify_quantiles(values, num_classes)
            
            # Remove duplicate breaks and limit to num_classes
            breaks = sorted(list(set(breaks)))
            if len(breaks) > num_classes + 1:
                indices = np.linspace(0, len(breaks) - 1, num_classes + 1, dtype=int)
                breaks = [breaks[i] for i in indices]
            
            # Get colors
            colors = self.get_color_scheme(color_scheme, num_classes)
            
            # Create ranges
            ranges = []
            for i in range(len(breaks) - 1):
                lower = breaks[i]
                upper = breaks[i + 1]
                
                # Ensure valid range
                if lower >= upper:
                    upper = lower + 0.0001
                
                # Create appropriate symbol with styling
                border_color_str = self.border_color.name()
                border_width = str(self.borderWidthSpinBox.value())
                
                color_with_alpha = colors[i % len(colors)].name()
                
                if layer.geometryType() == 2:  # Polygon
                    symbol = QgsFillSymbol.createSimple({
                        'color': color_with_alpha,
                        'color_border': border_color_str,
                        'outline_color': border_color_str,
                        'outline_width': border_width
                    })
                elif layer.geometryType() == 1:  # Line
                    symbol = QgsLineSymbol.createSimple({
                        'color': color_with_alpha,
                        'width': border_width
                    })
                else:  # Point
                    symbol = QgsMarkerSymbol.createSimple({
                        'color': color_with_alpha,
                        'size': '5',
                        'outline_color': border_color_str
                    })
                
                # Set opacity on the symbol itself
                symbol.setOpacity(opacity)
                
                # Create label
                if lower == upper:
                    label = f"{lower:.2f}"
                else:
                    label = f"{lower:.2f} - {upper:.2f}"
                
                ranges.append(QgsRendererRange(lower, upper, symbol, label))
            
            progress.setValue(66)
            
            # Create graduated renderer
            renderer = QgsGraduatedSymbolRenderer(field_name, ranges)
            
            # Apply renderer
            layer.setRenderer(renderer)
            
            # Handle NULL/Non-numeric values - HIDE THEM
            if null_features:
                # Create INVISIBLE symbol for NULL values
                if layer.geometryType() == 2:  # Polygon
                    null_symbol = QgsFillSymbol.createSimple({
                        'color': '255,255,255,0',  # Fully transparent
                        'outline_color': '255,255,255,0',
                        'outline_width': '0'
                    })
                elif layer.geometryType() == 1:  # Line
                    null_symbol = QgsLineSymbol.createSimple({
                        'color': '255,255,255,0',
                        'width': '0'
                    })
                else:  # Point
                    null_symbol = QgsMarkerSymbol.createSimple({
                        'color': '255,255,255,0',
                        'size': '0',
                        'outline_color': '255,255,255,0'
                    })
                
                # Apply invisible symbol to NULL features
                for feat_id in null_features:
                    feat = layer.getFeature(feat_id)
                    if feat.isValid():
                        feat_symbol = null_symbol.clone()
                        renderer.setSymbolForFeatureId(feat_id, feat_symbol)
            
            progress.setValue(85)
            
            # Enable labels if checkbox is checked
            if self.labelCheckBox.isChecked():
                label_field = self.labelFieldCombo.currentText()
                font_size = self.fontSizeSpinBox.value()
                font_color = self.label_font_color
                bg_color = self.label_bg_color
                bg_enabled = self.bgEnabledCheckBox.isChecked()
                
                # Use proper QGIS 3.x labeling API
                label_settings = QgsPalLayerSettings()
                label_settings.fieldName = label_field
                
                # Text format
                text_format = QgsTextFormat()
                text_format.setSize(font_size)
                text_format.setColor(font_color)
                
                # Buffer (background)
                if bg_enabled:
                    buffer_settings = QgsTextBufferSettings()
                    buffer_settings.setEnabled(True)
                    buffer_settings.setSize(1.0)
                    buffer_settings.setColor(bg_color)
                    text_format.setBuffer(buffer_settings)
                
                label_settings.setFormat(text_format)
                label_settings.enabled = True
                
                # Set placement based on geometry type (using Qgis enum)
                if layer.geometryType() == 0:  # Point
                    label_settings.placement = Qgis.LabelPlacement.AroundPoint
                elif layer.geometryType() == 1:  # Line
                    label_settings.placement = Qgis.LabelPlacement.Line
                else:  # Polygon
                    label_settings.placement = Qgis.LabelPlacement.OverPoint
                
                # Apply labeling
                labeling = QgsVectorLayerSimpleLabeling(label_settings)
                layer.setLabeling(labeling)
                layer.setLabelsEnabled(True)
            else:
                layer.setLabelsEnabled(False)
            
            # Final refresh
            layer.triggerRepaint()
            self.iface.layerTreeView().refreshLayerSymbology(layer.id())
            self.iface.mapCanvas().refresh()
            
            # Zoom to layer
            canvas = self.iface.mapCanvas()
            canvas.setExtent(layer.extent())
            canvas.refresh()
            
            progress.setValue(100)
            progress.close()
            
            # Show success message
            msg = f"✅ Thematic map created successfully!\n\n"
            msg += f"• Field: {field_name}\n"
            msg += f"• Method: {classification_method}\n"
            msg += f"• Classes: {num_classes}\n"
            msg += f"• Color scheme: {color_scheme}\n"
            msg += f"• Features with numeric data: {valid_count}\n"
            
            if null_features:
                null_count = len(null_features)
                msg += f"• Features hidden (no numeric data): {null_count}\n"
            
            self.iface.messageBar().pushSuccess("Success", msg)
            
            # Close dialog
            self.close()
            
        except Exception as e:
            try:
                progress.close()
            except:
                pass
            
            error_msg = f"Error creating thematic map:\n\n{str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Error", error_msg)
            self.iface.messageBar().pushCritical("Error", f"Failed: {str(e)}")