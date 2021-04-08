import vtk
from vtk.util import numpy_support
from vtk.util.vtkConstants import *
import numpy as np

from os import listdir
from os.path import isfile, join
import re

from skimage.color import rgb2gray


# numpy array (store load image data/matrix) to VTK image importer
# not correct
def numpy2VTKimporter(img,spacing=[1.0,1.0,1.0], origin=[0.0,0.0,0.0]):

    dim = img.shape
    print("dim", dim)

    
    # reshape the numpy array to (512,512,256)
    # img = img.reshape(dim[0], dim[1], dim[2])
    
    importer = vtk.vtkImageImport()
            
    img_data = img.astype('uint8')
    # img_string = img_data.tobytes() # type short
    img_string = img_data.tostring() # type short   
    
            
    # importer.CopyImportVoidPointer(img_data, img_data.nbytes)
    importer.CopyImportVoidPointer(img_string, len(img_string))
    importer.SetDataScalarType(VTK_UNSIGNED_CHAR)
    importer.SetNumberOfScalarComponents(1)
            
    extent = importer.GetDataExtent()
    print("extent",extent)

                 
    importer.SetDataExtent( extent[0], extent[0] + dim[2] - 1,
                extent[2], extent[2] + dim[1] - 1,
                extent[4], extent[4] + dim[0] - 1)
    importer.SetWholeExtent( extent[0], extent[0] + dim[2] - 1,
                 extent[2], extent[2] + dim[1] - 1,
                 extent[4], extent[4] + dim[0] - 1)

    
    importer.SetDataSpacing( spacing[0], spacing[1], spacing[2])
    #importer.SetDataOrigin( origin[0], origin[1], origin[2] )
    return importer



# imagefolderpath = "/home/kenan/Documents/DataRoom/US_calibration/rob_cali"
# imagefolderpath = "/home/kenan/Documents/DataRoom/US_calibration/img5"
imagefolderpath ='/home/kenan/Documents/pyDev/bmode3dreconstruction/recon_li/raw_8'

# imagefolderpath = "/home/kenan/Desktop/forearm US reconstruction/6-1-2021/v_img2"
# imagefolderpath = "/home/kenan/Documents/development/DLcode/DL_images/Bscan_US/image2"


onlyfiles = [f for f in listdir(imagefolderpath) if isfile(join(imagefolderpath, f))]
onlyfiles.sort(key=lambda f: int(re.sub('\D', '', f)))
sizeofimgs = len(onlyfiles)
# print (onlyfiles)
imagepathlist =onlyfiles


png_reader = vtk.vtkPNGReader()
png_reader.SetFileName(join(imagefolderpath, imagepathlist[0]))
png_reader.Update()
print(png_reader.GetOutput().GetDimensions())

rows,cols,_ = png_reader.GetOutput().GetDimensions()

data_3d = np.zeros([len(imagepathlist),cols, rows])
print("data_3d initial size", data_3d.shape)

for i in range(len(imagepathlist)):
    png_reader.SetFileName(join(imagefolderpath, imagepathlist[i]))
    png_reader.Update()
    img_data = png_reader.GetOutput()
    # print(img_data)

    sc = img_data.GetPointData().GetScalars()
    a = numpy_support.vtk_to_numpy(sc)
    # print("a shape", a.shape)
    a = a.reshape(cols,rows, -1)
    gray = rgb2gray(a)*255
    # gray = np.mean(a, axis=2)
    # print("gray shape", gray.shape)
    # data_3d[:,:,i] = gray
    data_3d[i] = gray

print(data_3d.shape)
print("max ---", np.max(data_3d))


vtkImage3D = numpy2VTKimporter(data_3d, spacing=[1,1,1], origin=[0.0,0.0,0.0])
print("GetDataExtent", vtkImage3D.GetDataExtent())
print ("vtkimporter-extent: ", vtkImage3D.GetWholeExtent())
print ("vtkimporter-spacing: ", vtkImage3D.GetDataSpacing())
print ("vtkimporter-origin: ", vtkImage3D.GetDataOrigin())



# # marching cube to etxtract surface 
# dmc = vtk.vtkDiscreteMarchingCubes()
# dmc.SetInputConnection(vtkImage3D.GetOutputPort())
# dmc.SetValue(0, 1)
# dmc.Update()

# #clean 
# cleanFilter = vtk.vtkCleanPolyData()
# cleanFilter.SetInputConnection(dmc.GetOutputPort())
# cleanFilter.Update()


# mapper = vtk.vtkPolyDataMapper()
# mapper.SetInputConnection(cleanFilter.GetOutputPort())

# actor = vtk.vtkActor()
# actor.SetMapper(mapper)
# actor.GetProperty().SetColor([255,0,0])
# ren.AddActor(actor)


colors = vtk.vtkNamedColors()
colors.SetColor('BkgColor', [51, 77, 102, 255])
ren = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)



volumeColor = vtk.vtkColorTransferFunction()
volumeColor.AddRGBPoint(0, 0.0, 0.0, 0.0)
volumeColor.AddRGBPoint(50, 1.0, 0.5, 0.3)
volumeColor.AddRGBPoint(100, 1.0, 0.5, 0.3)
volumeColor.AddRGBPoint(200, 1.0, 1.0, 0.9)

# The opacity transfer function is used to control the opacity
# of different tissue types.
volumeScalarOpacity = vtk.vtkPiecewiseFunction()
volumeScalarOpacity.AddPoint(0, 0.00)
volumeScalarOpacity.AddPoint(50, 0.5)
volumeScalarOpacity.AddPoint(100, 0.8)
volumeScalarOpacity.AddPoint(200, 0.85)

# The gradient opacity function is used to decrease the opacity
# in the 'flat' regions of the volume while maintaining the opacity
# at the boundaries between tissue types.  The gradient is measured
# as the amount by which the intensity changes over unit distance.
# For most medical data, the unit distance is 1mm.
volumeGradientOpacity = vtk.vtkPiecewiseFunction()
volumeGradientOpacity.AddPoint(0, 0.0)
volumeGradientOpacity.AddPoint(90, 0.5)
volumeGradientOpacity.AddPoint(100, 1.0)



#-------------------------------------------------
# working on the GPU
volumeMapper = vtk.vtkGPUVolumeRayCastMapper()
volumeMapper.SetInputConnection(vtkImage3D.GetOutputPort())

#-------------------------------------------------
# # working on the CPU
# # The volume will be displayed by ray-cast alpha compositing.
# # A ray-cast mapper is needed to do the ray-casting.
# volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()
# volumeMapper.SetInputConnection(vtkImage3D.GetOutputPort())



volumeProperty = vtk.vtkVolumeProperty()
volumeProperty.SetColor(volumeColor)
volumeProperty.SetScalarOpacity(volumeScalarOpacity)
volumeProperty.SetGradientOpacity(volumeGradientOpacity)
volumeProperty.SetInterpolationTypeToLinear()
volumeProperty.ShadeOn()
volumeProperty.SetAmbient(0.4)
volumeProperty.SetDiffuse(0.6)
volumeProperty.SetSpecular(0.2)
# volumeMapper.Update()





# The vtkVolume is a vtkProp3D (like a vtkActor) and controls the position
# and orientation of the volume in world coordinates.
volume = vtk.vtkVolume()
volume.SetMapper(volumeMapper)
volume.SetProperty(volumeProperty)

# Finally, add the volume to the renderer
ren.AddViewProp(volume)


# Set up an initial view of the volume.  The focal point will be the
# center of the volume, and the camera position will be 400mm to the
# patient's left (which is our right).
camera = ren.GetActiveCamera()
c = volume.GetCenter()
camera.SetViewUp(0, 0, -1)
camera.SetPosition(c[0], c[1] - 400, c[2])
camera.SetFocalPoint(c[0], c[1], c[2])
camera.Azimuth(30.0)
camera.Elevation(30.0)

# Set a background color for the renderer
ren.SetBackground(colors.GetColor3d('BkgColor'))

# Increase the size of the render window
renWin.SetSize(640, 480)
renWin.SetWindowName('MedicalDemo4')

# Interact with the data.
iren.Start()