import sys
import vtk

# 确保脚本的第一个参数是文件路径
if len(sys.argv) < 2:
    print("No file path provided")
    sys.exit(1)

vtk_file = sys.argv[1]  # 获取传递的文件路径

print(f"Loading VTK file: {vtk_file}")

# 创建渲染器、渲染窗口和交互器
renderer = vtk.vtkRenderer()
render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)

render_window_interactor = vtk.vtkRenderWindowInteractor()
render_window_interactor.SetRenderWindow(render_window)

# 读取 VTK 文件
reader = vtk.vtkUnstructuredGridReader()
reader.SetFileName(vtk_file)
reader.Update()

# 为文件创建一个 mapper 和 actor
mapper = vtk.vtkDataSetMapper()
mapper.SetInputConnection(reader.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)

# 将 actor 添加到渲染器中
renderer.AddActor(actor)

# 设置背景色
renderer.SetBackground(0.1, 0.1, 0.1)

# 启动渲染并交互
render_window.Render()
render_window_interactor.Start()
