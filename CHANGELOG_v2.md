# One Click Thematic Map v2.0 - Feature Update

## ✨ New Features Added

### 1. **Classification Methods** 
- **Equal Intervals**: Divides data range into equal-sized classes
- **Quantiles**: Each class contains approximately equal number of features
- **Natural Breaks (Jenks)**: Optimized breaks that minimize within-group variance
- **Pretty Breaks**: Creates aesthetically pleasing round numbers
- **Standard Deviation**: Classes based on statistical distribution

### 2. **Color Customization**
- **Custom Color Picker**: Choose custom minimum and maximum colors
- **Reverse Colors**: Toggle to reverse color scheme direction
- **Pre-built Schemes**: Added Orange scheme (total 8 color schemes)
- **Gradient Generation**: Automatically generates smooth gradients between colors

### 3. **Map Styling**
- **Border Color Control**: Custom color picker for feature borders
- **Border Width Adjustment**: 0-5 mm adjustable border width
- **Opacity/Transparency**: Slider to control layer transparency (0-100%)
- **Dynamic Updates**: Real-time preview of styling changes

### 4. **Export & Save**
- **Save Style**: Save current settings as JSON preset
- **Load Style**: Load previously saved style presets
- **Export as QML**: Export layer styling in QGIS QML format
- **Auto Styles Directory**: Automatic `saved_styles/` folder creation

## 📊 Enhanced UI

- **Scrollable Dialog**: Expanded interface to accommodate new controls
- **Organized Sections**:
  - Layer & Field Selection
  - Classification Method
  - Color Customization
  - Map Styling
  - Export & Save

## 🔧 Technical Improvements

- Added **NumPy** support for advanced classification calculations
- **Jenkins Breaks** support (auto-fallback to quantiles if not installed)
- **Color alpha blending** for smooth gradient generation
- **JSON persistence** for style presets
- Better error handling and user feedback

## 📋 UI Controls

| Control | Range | Default |
|---------|-------|---------|
| Classes | 2-15 | 5 |
| Border Width | 0-5 mm | 0.2 mm |
| Opacity | 0-100% | 100% |
| Color Schemes | 8 options + Custom | Blue |

## 💾 New Directories

- `saved_styles/` - For storing JSON style presets

## Version Info
- **Version**: 2.0
- **Previous**: 1.0 (single click, basic quantile classification)
- **Author**: Prince
- **Updated**: January 29, 2026
