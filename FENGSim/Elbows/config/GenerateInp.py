"""
Description:     Automatically generates inp files based on configuration files.
Author:          Li Shizhe
Date:            2025-07-16
Version:         v1.0
"""

import re
import os
import yaml
import textwrap


def find_face_elements(elements, surface_data):
    """
    高效查找面所属的体单元和面编号

    Args:
        elements: 单元列表，每个单元是节点列表
        faces: 面列表，每个面是节点列表

    Returns:
        结果列表，包含每个面的查找结果
    """

    # 定义单元类型的面拓扑关系（基于1的索引转换为基于0的索引）
    ELEMENT_FACE_TOPOLOGY = {
        4: {  # 四面体 (4个节点)
            'type': 'tetrahedron',
            'faces': [
                [0, 1, 2],  # Face 1: 1-2-3
                [0, 3, 1],  # Face 2: 1-4-2
                [1, 3, 2],  # Face 3: 2-4-3
                [2, 3, 0],  # Face 4: 3-4-1
            ]
        },
        8: {  # 六面体 (8个节点)
            'type': 'hexahedron',
            'faces': [
                [0, 1, 2, 3],  # Face 1: 1-2-3-4
                [4, 7, 6, 5],  # Face 2: 5-8-7-6
                [0, 4, 5, 1],  # Face 3: 1-5-6-2
                [1, 5, 6, 2],  # Face 4: 2-6-7-3
                [2, 6, 7, 3],  # Face 5: 3-7-8-4
                [3, 7, 4, 0],  # Face 6: 4-8-5-1
            ]
        }
    }

    # 构建面到单元的哈希映射表
    face_to_element = {}

    for elem_idx, element in enumerate(elements):
        node_count = len(element)

        if node_count not in ELEMENT_FACE_TOPOLOGY:
            print(f"警告: 不支持的单元类型，节点数: {node_count}")
            continue

        topology = ELEMENT_FACE_TOPOLOGY[node_count]

        # 为当前单元的每个面创建映射
        for face_idx, face_nodes_indices in enumerate(topology['faces']):
            # 获取面的实际节点编号
            face_nodes = [element[i] for i in face_nodes_indices]

            # 使用排序后的节点作为哈希键，确保面的方向无关性
            face_key = tuple(sorted(face_nodes))

            # 存储单元索引、单元类型和面编号
            face_to_element[face_key] = {
                'element_index': elem_idx,
                'element_type': topology['type'],
                'face_number': face_idx + 1,  # 面编号从1开始
                'face_nodes': face_nodes
            }

    # 查找每个面所属的单元
    for surface_name, data in surface_data.items():
        for face_idx, face in enumerate(data['surfaces']):
            face_key = tuple(sorted(face))

            if face_key in face_to_element:
                element_info = face_to_element[face_key]

                data['surfaces'][face_idx].extend([f'S{element_info["face_number"]}', element_info['element_index']])


                # print(f"面 {face_idx}: {face} -> "
                #       f"单元 {element_info['element_index']} "
                #       f"({element_info['element_type']}) "
                #       f"的第 {element_info['face_number']} 面")
            else:
                print(f"面 {face_idx}: {face} -> 未找到对应的单元面")



def process_geometry_file(geo_file: str, output_file: str,
                     volume_mappings: dict,
                     surface_mappings: dict):
    """
    处理Abaqus .inp文件,提取节点和体积单元,以及多个指定表面的节点

    参数:
    geo_file: 输入文件名
    output_file: 输出文件名
    volume_mappings: 字典，格式为 {'Volume1': 'Tube', 'Volume2': 'Rotation-Tube', ...}
    surface_mappings: 字典，格式为 {'Surface1': 'Tube-outer', 'Surface8': 'Rotation-Tube-inner', ...}
    """


    # 检查输入文件是否存在
    if not os.path.exists(geo_file):
        print(f"错误：找不到文件 {geo_file}")
        return

    nodes = []
    volume_data = {
        'elements':[],
        'volumes': {}
    }
    surface_data = {}

    # 初始化每个表面的节点集合
    for original_name in surface_mappings.keys():
        surface_data[original_name] = {
            'nodes': set(),
            'surfaces': [],
            'elements':[]
        }

    print(f"将要处理的体映射:")
    for old_name, new_name in volume_mappings.items():
        print(f"  {old_name} -> {new_name}")
    print()

    print(f"将要处理的表面映射:")
    for old_name, new_name in surface_mappings.items():
        print(f"  {old_name} -> {new_name}")
    print()

    def extract_elset_value(line):
        """
        从行中提取 ELSET= 后面的值
        支持多种格式：
        - ELSET=Surface1
        - ELSET=Surface1,
        - type=CPS3, ELSET=Surface1
        - type=CPS3, ELSET=Surface1, 其他参数
        """
        # 使用正则表达式匹配 ELSET= 后面的值
        # 匹配 ELSET= 后面的非空白、非逗号字符
        match = re.search(r'ELSET=([^,\s]+)', line, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    with open(geo_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 处理 NODE 部分
        if line.startswith('*NODE'):
            print("正在处理节点...")
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('*'):
                node_line = lines[i].strip()
                if node_line:  # 跳过空行
                    nodes.append(node_line)
                i += 1
            continue

        # 处理 ELEMENT 部分
        elif line.startswith('*ELEMENT'):
            if 'ELSET=Volume' in line:
                print(f"正在处理体积单元: {line}")

                elset_value = extract_elset_value(line)

                flag = False
                for volume_name in volume_mappings.keys():
                    # 使用正则查找 ELSET= 后面的内容
                    if elset_value == volume_name:
                        flag = True
                        elset_value = volume_mappings[volume_name]
                        break

                start_index = len(volume_data['elements']) + 1
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('*'):
                    element_line = lines[i].strip().split(', ')[1:]
                    if element_line:
                        volume_data['elements'].append(element_line)
                    i += 1
                end_index = len(volume_data['elements'])
                if flag:
                    volume_data['volumes'][elset_value]=[start_index, end_index]
                continue

            # 检查是否是指定的表面单元
            else:
                elset_value = extract_elset_value(line)
                surface_found = None

                for surface_name in surface_mappings.keys():
                    # 使用正则查找 ELSET= 后面的内容
                    if elset_value == surface_name:
                        surface_found = surface_name
                        break

                if surface_found:
                    print(f"正在处理表面单元: {line}")
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('*'):
                        surface_line = lines[i].strip().split(', ')[1:]
                        if surface_line:
                            # 保存完整的单元信息
                            surface_data[surface_found]['surfaces'].append(surface_line)
                            # 提取节点编号
                            for node_id in surface_line[0:]:
                                try:
                                    surface_data[surface_found]['nodes'].add(int(node_id.strip()))
                                except ValueError:
                                    pass  # 跳过无法转换为整数的值
                        i += 1
                    continue

        i += 1

    # 确定面的所属单元及编号
    find_face_elements(volume_data['elements'], surface_data)

    # 写入输出文件
    output_path = os.path.join(os.path.dirname(geo_file) if os.path.dirname(geo_file) else '.', output_file)

    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入节点
        f.write('*NODE\n')
        for node in nodes:
            f.write(f'{node}\n')
        f.write('\n')

        # 写入所有体积单元（重新编号从1开始）
        if volume_data['elements']:
            f.write('*ELEMENT, type=C3D4\n')
            for idx, element in enumerate(volume_data['elements'], 1):
                f.write(f"{idx}, {', '.join(element)}\n")
            f.write('\n')

        # 写入所有体的信息
        for original_name, new_name in volume_mappings.items():
            f.write(f'*Elset, elset={new_name}, generate\n')
            f.write(f' {volume_data['volumes'][new_name][0]}, {volume_data['volumes'][new_name][1]}, 1\n')
        f.write('\n')

        # 写入每个表面的信息
        for original_name, new_name in surface_mappings.items():
            surfaces = surface_data[original_name]['surfaces']
            if surfaces:
                f.write(f'*SURFACE, NAME={new_name}, TYPE=ELEMENT\n')
                for i in range(0, len(surfaces), 1):
                    info = [surfaces[i][-1], surfaces[i][-2]]
                    f.write(', '.join(map(str, info)) + '\n')
                f.write('\n')

    # 输出统计信息
    print(f"\n处理完成!")
    print(f"- 节点数量: {len(nodes)}")
    print(f"- 体积单元数量: {len(volume_data['elements'])}")

    for original_name, new_name in volume_mappings.items():
        element_count = volume_data['volumes'][new_name][1] - volume_data['volumes'][new_name][0] + 1
        if element_count > 0:
            print(f"- 体 {original_name} -> {new_name}: {element_count} 个单元")
        else:
            print(f"- 警告: 体 {original_name} 未找到或无数据")

    for original_name, new_name in surface_mappings.items():
        node_count = len(surface_data[original_name]['nodes'])
        element_count = len(surface_data[original_name]['surfaces'])
        if node_count > 0:
            print(f"- 表面 {original_name} -> {new_name}: {node_count} 个节点, {element_count} 个单元")
        else:
            print(f"- 警告: 表面 {original_name} 未找到或无数据")

    print(f"- 输出文件: {output_path}")

    return len(nodes)


def output_inp_SI(output_file, config: dict):

    name = config.get('General', {}).get('Name')
    linear_elastic = config.get('Models', {}).get('LinearElastic', {})

    # 检查输出文件是否存在
    if not os.path.exists(output_file):
        print(f"错误：找不到文件 {output_file}")
        return

    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(f"*Material,name={name}\n")
        f.write("*Density\n")
        density = linear_elastic.get('Density', '')
        val, unit = density.split(' ', 1)
        f.write(f"{val:.6e},\n")
        f.write("*Elastic\n")
        youngs = linear_elastic.get('YoungsModulus', '')
        val, unit = youngs.split(' ', 1)
        possion = linear_elastic.get('PoissonRatio', '')
        f.write(f"{val}, {possion}\n")
        # f.write("*Plastic\n")


def output_inp_SI_mm(output_file, config: dict):

    name = config.get('General', {}).get('Name')
    linear_elastic = config.get('Models', {}).get('LinearElastic', {})

    # 检查输出文件是否存在
    if not os.path.exists(output_file):
        print(f"错误：找不到文件 {output_file}")
        return

    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(f"*Material,name={name}\n")
        f.write("*Density\n")
        density = linear_elastic.get('Density', '')
        val, unit = density.split(' ', 1)
        f.write(f"{float(val) * 1e-12:.6e},\n")
        f.write("*Elastic\n")
        youngs = linear_elastic.get('YoungsModulus', '')
        val, unit = youngs.split(' ', 1)
        possion = linear_elastic.get('PoissonRatio', '')
        f.write(f"{val}, {possion}\n")
        # f.write("*Plastic\n")
        f.write("\n")

    return name

def process_matsec_file(mat_file: str, output_file: str,
                     volume_mappings: dict):

    # 检查输入文件是否存在
    if not os.path.exists(mat_file):
        print(f"错误：找不到文件 {mat_file}")
        return

    with open(mat_file, 'r', encoding='utf-8') as f:
        mat_config = yaml.safe_load(f)
    unique_mat = list(set(mat_config.values()))

    for mat in unique_mat:
        with open(mat, 'r', encoding='utf-8') as f:
            mat_info = yaml.safe_load(f)
        name = output_inp_SI_mm(output_file, mat_info)
        for k, v in mat_config.items():
            if v == mat:
                mat_config[k] = name

    with open(output_file, 'a', encoding='utf-8') as f:
        for vol, mat in mat_config.items():
            f.write(f"*Solid Section, elset={volume_mappings[vol]}, material={mat}\n")

def process_rigidbody_file(rigid_file: str, output_file: str,
                     volume_mappings: dict, nodes_num):

    # 检查输入文件是否存在
    if not os.path.exists(rigid_file):
        print(f"错误：找不到文件 {rigid_file}")
        return

    with open(rigid_file, 'r', encoding='utf-8') as f:
        rigid_config = yaml.safe_load(f)

    # 检查输出文件是否存在
    if not os.path.exists(output_file):
        print(f"错误：找不到文件 {output_file}")
        return


    with open(output_file, 'a', encoding='utf-8') as f:
        f.write("\n*NODE\n")
        tmp_num = nodes_num
        for volume, nodes in rigid_config.items():
            tmp_num += 1
            nodes_str = str(nodes['ref']).replace('(', '').replace(')', '').replace(',', ',   ')
            f.write(f"{tmp_num},  {nodes_str}\n")
            tmp_num += 1
            nodes_str = str(nodes['rot']).replace('(', '').replace(')', '').replace(',', ',   ')
            f.write(f"{tmp_num},  {nodes_str}\n")
        f.write("\n")
        tmp_num = nodes_num
        for volume, nodes in rigid_config.items():
            tmp_num += 1
            f.write(f"*Nset, nset={volume_mappings[volume]}_ref\n")
            f.write(f"{tmp_num}\n")
            tmp_num += 1
            f.write(f"*Nset, nset={volume_mappings[volume]}_rot\n")
            f.write(f"{tmp_num}\n")
        f.write("\n")
        tmp_num = nodes_num
        for volume, nodes in rigid_config.items():
            f.write(f"*Rigid Body, elset={volume_mappings[volume]}, ref node={tmp_num+1}, rot node={tmp_num+2}\n")
            tmp_num += 2


def process_contact_file(contact_file: str, output_file: str):

    # 检查输入文件是否存在
    if not os.path.exists(contact_file):
        print(f"错误：找不到文件 {contact_file}")
        return

    # 读取 contact_file 的内容
    with open(contact_file, 'r') as f_contact:
        contact_content = f_contact.read()

    # 追加到 output_file 末尾
    with open(output_file, 'a') as f_output:
        f_output.write("\n")
        f_output.write(contact_content)


def process_step_file(step_file: str,output_file: str):

    # 定义需要修改的内容
    data = {
        "amp_name": "AMP-1",
        "amp_values": "0.,              0.,              1.,              1.",
        "rotation_ref": "Rotation-Tube_ref",
        "rotation_rot": "Rotation-Tube_rot",
        "fixed_ref": "Fixed-Tube_ref",
        "fixed_rot": "Fixed-Tube_rot",
        "circle_ref": "Rotation-Circle_ref",
        "circle_rot": "Rotation-Circle_rot",
        "step_name": "Step-1",
        "nlgeom": "YES",
        "inc": 1000000,
        "static_values": "1e-2, 3., 1e-08, 1",
        "boundary_amp": "AMP-1",
        "rotation_value": "-1.5708",
        "node_file_freq": 1,
        "el_file": "S,PE"
    }

    with open(step_file, 'r', encoding='utf-8') as f_step:
        step_content = yaml.safe_load(f_step)

    data["rotation_value"] = -step_content["angle"]
    data["static_values"] = step_content["step"]


    # 追加到 output_file 末尾
    content = f"""
    *Amplitude, name={data['amp_name']}
             {data['amp_values']}

    *Boundary
    {data['rotation_ref']}, 1, 3
    *Boundary
    {data['rotation_rot']}, 1, 3
    *Boundary
    {data['fixed_ref']}, 1, 3
    *Boundary
    {data['fixed_rot']}, 1, 3
    *Boundary
    {data['circle_ref']}, 1, 3
    *Boundary
    {data['circle_rot']}, 1, 3

    *Step, name={data['step_name']}, nlgeom={data['nlgeom']}, inc={data['inc']}
    *Static
    {data['static_values']}

    *Boundary, amplitude={data['boundary_amp']}
    {data['rotation_rot']}, 1, 1, {data['rotation_value']}
    *Boundary, amplitude={data['boundary_amp']}
    {data['circle_rot']}, 1, 1, {data['rotation_value']}

    ** 结果输出
    *node file, frequency={data['node_file_freq']}
    U
    *el file
    {data['el_file']}
    *end step
    """

    with open(output_file, 'a') as f_output:
        f_output.write("\n")
        f_output.write(textwrap.dedent(content))

if __name__ == "__main__":
    # 示例用法
    print("=== Abaqus & CCX .inp 文件处理工具 ===\n")
    # 检查当前工作目录
    print("Current working directory:", os.getcwd())
    os.chdir("/home/ysy/FENGSim/starter/FENGSim/Elbows/config/")
    print("Current working directory:", os.getcwd())

    # 读取配置文件
    with open('config.ini', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 调用网格处理函数
    nodes_num = process_geometry_file(
        config['geo_file'],
        config['output_file'],
        config['volume_mappings'],
        config['surface_mappings']
    )

    # 调用材料处理函数
    process_matsec_file(config['mat_file'],
                        config['output_file'],
                        config['volume_mappings'])

    # 调用刚体约束函数
    process_rigidbody_file(config['rigid_file'],
                           config['output_file'],
                           config['volume_mappings'],
                           nodes_num)

    # 调用接触处理函数
    process_contact_file(config['contact_file'], config['output_file'])

    # 调用载荷和分析步处理函数
    process_step_file(config['step_file'], config['output_file'])
