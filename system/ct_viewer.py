import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import SimpleITK as sitk
import numpy as np
import vtk.util.numpy_support as vtk_np
import vtk
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkInteractionWidgets import vtkResliceCursor, vtkResliceCursorWidget, vtkResliceCursorLineRepresentation
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkActor, vtkPolyDataMapper, vtkCamera
from vtkmodules.vtkIOImage import vtkImageImport
from vtkmodules.vtkFiltersCore import vtkMarchingCubes
from vtkmodules.util.vtkConstants import VTK_FLOAT
import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingOpenGL2

# Ensures compatibility with macOS for layering issues with PyQt5 and VTK
os.environ["QT_MAC_WANTS_LAYER"] = "1"

class CTViewer(QWidget):
    def __init__(self, sitk_image, render_model=False):
        super().__init__()
        self.sitk_image = sitk_image  # SimpleITK image to visualize
        self.render_model = render_model  # Boolean to indicate if 3D model rendering is required
        self.image_data = self.sitk_to_vtk_image(sitk_image)  # Convert SimpleITK image to VTK image
        self.reslice_cursor = vtkResliceCursor()  # Create a reslice cursor for slice views
        self.reslice_cursor.SetCenter(self.image_data.GetCenter())  # Set the cursor to the image center
        self.reslice_cursor.SetImage(self.image_data)
        self.reslice_cursor.SetThickMode(False)  # Disable thick mode for thinner slices
        self.reslice_widgets = []  # List to store reslice widgets for each view
        self.reslice_representations = []  # List to store representations for reslice widgets
        self.init_ui()  # Initialize the user interface layout
        self.setup_reslice_views()  # Set up the slice views (axial, coronal, sagittal)
        self.synchronize_views()  # Add interactivity to keep views in sync
        self.setup_model_view()  # Prepare 3D model view (if render_model is True)
        if self.render_model:
            self.generate_and_display_model()  # Generate and display 3D model if specified

    def init_ui(self):
        # Set up main layout with slice views and 3D model view
        main_layout = QVBoxLayout(self)
        reslice_layout = QHBoxLayout()
        
        # Define widgets for axial, coronal, and sagittal views
        self.vtkWidget_axial = QWidget()
        self.vtkWidget_coronal = QWidget()
        self.vtkWidget_sagittal = QWidget()
        
        # Set minimum sizes for the views
        self.vtkWidget_axial.setMinimumSize(200, 200)
        self.vtkWidget_coronal.setMinimumSize(200, 200)
        self.vtkWidget_sagittal.setMinimumSize(200, 200)
        
        # Add views to the layout
        reslice_layout.addWidget(self.vtkWidget_axial)
        reslice_layout.addWidget(self.vtkWidget_coronal)
        reslice_layout.addWidget(self.vtkWidget_sagittal)
        main_layout.addLayout(reslice_layout)

        # Define and add the 3D model view
        self.model_vtkWidget = QWidget()
        self.model_vtkWidget.setMinimumSize(600, 400)
        main_layout.addWidget(self.model_vtkWidget)
        self.setLayout(main_layout)

    def setup_reslice_views(self):
        # Set up individual reslice views (axial, coronal, sagittal)
        self.vtkWidget_axial = self.setup_reslice_view(self.vtkWidget_axial, 2)
        self.vtkWidget_coronal = self.setup_reslice_view(self.vtkWidget_coronal, 1)
        self.vtkWidget_sagittal = self.setup_reslice_view(self.vtkWidget_sagittal, 0)

    def sitk_to_vtk_image(self, sitk_image):
        # Convert SimpleITK image to VTK image
        size = sitk_image.GetSize()
        spacing = sitk_image.GetSpacing()
        origin = sitk_image.GetOrigin()
        image_array = sitk.GetArrayFromImage(sitk_image)  # Convert SITK image to NumPy array
        image_array = np.transpose(image_array.astype(np.float32), (2, 1, 0)).flatten(order='F')
        vtk_image = vtkImageData()
        vtk_image.SetDimensions(size)
        vtk_image.SetSpacing(spacing)
        vtk_image.SetOrigin(origin)
        vtk_image.AllocateScalars(VTK_FLOAT, 1)
        vtk_data_array = vtk.util.numpy_support.vtk_to_numpy(vtk_image.GetPointData().GetScalars())
        vtk_data_array[:] = image_array  # Assign pixel data to VTK image
        return vtk_image

    def setup_reslice_view(self, placeholder_widget, orientation):
        # Setup for each individual reslice view
        render_window_interactor = QVTKRenderWindowInteractor(placeholder_widget)
        layout = QVBoxLayout(placeholder_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(render_window_interactor)
        
        # Create and configure renderer for the view
        renderer = vtkRenderer()
        render_window_interactor.GetRenderWindow().AddRenderer(renderer)
        
        # Configure the reslice cursor representation and widget
        reslice_representation = vtkResliceCursorLineRepresentation()
        reslice_widget = vtkResliceCursorWidget()
        reslice_widget.SetInteractor(render_window_interactor)
        reslice_widget.SetRepresentation(reslice_representation)
        reslice_representation.GetResliceCursorActor().GetCursorAlgorithm().SetResliceCursor(self.reslice_cursor)
        reslice_representation.GetResliceCursorActor().GetCursorAlgorithm().SetReslicePlaneNormal(orientation)
        
        # Set window/level for the reslice representation
        scalar_range = self.image_data.GetScalarRange()
        reslice_representation.SetWindowLevel(scalar_range[1] - scalar_range[0], (scalar_range[1] + scalar_range[0]) / 2)
        
        # Input data for reslice view
        reslice_representation.GetReslice().SetInputData(self.image_data)
        reslice_representation.GetResliceCursor().SetImage(self.image_data)
        
        # Enable the reslice widget and add it to lists
        reslice_widget.SetEnabled(1)
        reslice_widget.On()
        self.reslice_widgets.append(reslice_widget)
        self.reslice_representations.append(reslice_representation)
        
        # Set camera orientation based on the slice plane
        renderer.ResetCamera()
        camera = renderer.GetActiveCamera()
        center = self.image_data.GetCenter()
        camera.SetFocalPoint(center)
        if orientation == 2:
            camera.SetPosition(center[0], center[1], center[2] + 1000)
            camera.SetViewUp(0, -1, 0)
        elif orientation == 1:
            camera.SetPosition(center[0], center[1] - 1000, center[2])
            camera.SetViewUp(0, 0, 1)
        elif orientation == 0:
            camera.SetPosition(center[0] - 1000, center[1], center[2])
            camera.SetViewUp(0, 0, 1)
        camera.SetParallelScale(max([dim * spc for dim, spc in zip(self.image_data.GetDimensions(), self.image_data.GetSpacing())]) / 2.0)
        
        # Initialize and render the interactor
        render_window_interactor.Initialize()
        render_window_interactor.Render()
        return render_window_interactor

    def synchronize_views(self):
        # Sync views so that interaction in one updates others
        for reslice_widget in self.reslice_widgets:
            reslice_widget.AddObserver("InteractionEvent", self.on_interaction)
            reslice_widget.AddObserver("EndInteractionEvent", self.on_interaction)

    def on_interaction(self, caller, event):
        # Callback function to update all reslice widgets on interaction
        for reslice_widget in self.reslice_widgets:
            if reslice_widget != caller:
                reslice_widget.Render()

    def setup_model_view(self):
        # Set up the layout and renderer for the 3D model view
        render_window_interactor = QVTKRenderWindowInteractor(self.model_vtkWidget)
        layout = QVBoxLayout(self.model_vtkWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(render_window_interactor)
        
        self.model_renderer = vtkRenderer()
        render_window = render_window_interactor.GetRenderWindow()
        render_window.AddRenderer(self.model_renderer)
        render_window_interactor.Initialize()
        self.model_vtkWidget = render_window_interactor

    def generate_and_display_model(self):
        # Generate a 3D model from the image data and display it
        self.model_renderer.RemoveAllViewProps()
        poly_data = self.generate_3d_model()
        mapper = vtkPolyDataMapper()
        mapper.SetInputData(poly_data)
        actor = vtkActor()
        actor.SetMapper(mapper)
        
        # Add actor to the renderer
        self.model_renderer.AddActor(actor)
        self.model_renderer.SetBackground(0.68, 0.85, 0.9)
        self.model_renderer.ResetCamera()
        self.model_vtkWidget.GetRenderWindow().Render()

    def generate_3d_model(self):
        # Generate 3D model using thresholding and marching cubes for surface extraction
        image_array = sitk.GetArrayFromImage(self.sitk_image).astype(np.float32)
        thresholded_image = np.where((image_array >= 300) & (image_array <= 3000), image_array, 0)
        shape = thresholded_image.shape
        flat_image_array = thresholded_image.flatten(order="C")
        
        importer = vtkImageImport()
        importer.CopyImportVoidPointer(flat_image_array, flat_image_array.nbytes)
        importer.SetDataScalarType(VTK_FLOAT)
        importer.SetNumberOfScalarComponents(1)
        importer.SetWholeExtent(0, shape[2] - 1, 0, shape[1] - 1, 0, shape[0] - 1)
        importer.SetDataExtent(0, shape[2] - 1, 0, shape[1] - 1, 0, shape[0] - 1)
        importer.SetDataSpacing(self.sitk_image.GetSpacing())
        importer.SetDataOrigin(self.sitk_image.GetOrigin())
        importer.Update()
        
        # Run marching cubes algorithm to generate a surface model
        vtk_image = importer.GetOutput()
        contour_filter = vtkMarchingCubes()
        contour_filter.SetInputData(vtk_image)
        contour_filter.SetValue(0, 300)
        contour_filter.Update()
        return contour_filter.GetOutput()

    def closeEvent(self, event):
        # Close event to finalize and clean up reslice widgets
        for widget in [self.vtkWidget_axial, self.vtkWidget_coronal, self.vtkWidget_sagittal, self.model_vtkWidget]:
            if widget:
                widget.Finalize()
                del widget
        super().closeEvent(event)

# Main execution of the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    image_path = '/Users/markxu/Downloads/001.mha'  # Path to medical image file
    sitk_image = sitk.ReadImage(image_path)  # Read the image using SimpleITK
    viewer = CTViewer(sitk_image)  # Create an instance of the viewer with the image
    viewer.show()  # Display the viewer window
    sys.exit(app.exec_())  # Execute the application