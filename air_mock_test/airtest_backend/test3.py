import cv2
import cv2.aruco as aruco
import numpy as np
import math
import time


class DronePoseEstimator:
    def __init__(self, camera_matrix, dist_coeffs, marker_size=0.5):
        """
        初始化无人机位姿估计器

        参数:
            camera_matrix: 相机内参矩阵
            dist_coeffs: 畸变系数
            marker_size: 标记实际物理尺寸（米）
        """
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        self.marker_size = marker_size

        # 创建ArUco检测器
        self.dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
        self.detector = aruco.ArucoDetector(self.dictionary, aruco.DetectorParameters())

        # 定义标记的3D坐标点（以标记中心为原点）
        half_size = marker_size / 2.0
        self.object_points = np.array([
            [-half_size, half_size, 0],  # 左上
            [half_size, half_size, 0],  # 右上
            [half_size, -half_size, 0],  # 右下
            [-half_size, -half_size, 0]  # 左下
        ], dtype=np.float32)

        # 统计信息
        self.last_pose = None
        self.pose_history = []

    def estimate_pose(self, frame, target_marker_id=None):
        """
        估计无人机相对于ArUco标记的位姿

        参数:
            frame: 摄像头捕获的图像帧
            target_marker_id: 目标标记ID，如果为None则使用检测到的第一个标记

        返回:
            pose_dict: 位姿信息字典
            None: 如果未检测到标记
        """
        # 检测ArUco标记
        corners, ids, rejected = self.detector.detectMarkers(frame)

        if ids is None or len(ids) == 0:
            return None

        # 如果指定了目标标记ID，找到对应的标记
        target_index = 0
        if target_marker_id is not None:
            target_indices = np.where(ids == target_marker_id)[0]
            if len(target_indices) == 0:
                return None
            target_index = target_indices[0]

        # 获取目标标记的角点
        target_corners = corners[target_index]
        marker_id = ids[target_index][0]

        # 使用solvePnP计算位姿
        success, rvec, tvec = cv2.solvePnP(
            self.object_points,
            target_corners,
            self.camera_matrix,
            self.dist_coeffs
        )

        if not success:
            return None

        # 计算详细位姿信息
        pose_info = self._calculate_detailed_pose(rvec, tvec, marker_id)

        # 保存当前位姿
        self.last_pose = pose_info
        self.pose_history.append(pose_info)

        return pose_info

    def _calculate_detailed_pose(self, rvec, tvec, marker_id):
        """
        计算详细的位姿信息
        """
        # 提取平移向量
        x = tvec[0][0]  # 横向偏移（米）
        y = tvec[1][0]  # 纵向偏移（米）
        z = tvec[2][0]  # 高度/垂直距离（米）

        # 计算距离
        distance = np.linalg.norm(tvec)

        # 计算水平距离（在XY平面上的投影）
        horizontal_distance = math.sqrt(x ** 2 + y ** 2)

        # 计算旋转矩阵
        rotation_matrix, _ = cv2.Rodrigues(rvec)

        # 计算欧拉角（roll, pitch, yaw）
        euler_angles = self._rotation_matrix_to_euler_angles(rotation_matrix)

        # 计算俯仰角（无人机相对于标记平面的倾斜角度）
        pitch_angle = math.atan2(z, horizontal_distance)  # 俯仰角

        # 计算方位角（无人机相对于标记的朝向角度）
        azimuth_angle = math.atan2(y, x)  # 方位角

        # 构建位姿信息字典
        pose_info = {
            'marker_id': marker_id,
            'timestamp': time.time(),

            # 平移信息
            'translation': {
                'x': x,  # 右为正，左为负
                'y': y,  # 下为正，上为负
                'z': z,  # 远为正，近为负
            },

            # 距离信息
            'distances': {
                'total': distance,  # 总距离
                'horizontal': horizontal_distance,  # 水平距离
                'vertical': z  # 垂直距离
            },

            # 旋转信息
            'rotation': {
                'vector': rvec.flatten().tolist(),  # 旋转向量
                'matrix': rotation_matrix.tolist(),  # 旋转矩阵
                'euler': euler_angles,  # 欧拉角
            },

            # 角度信息
            'angles': {
                'pitch': math.degrees(pitch_angle),  # 俯仰角（度）
                'azimuth': math.degrees(azimuth_angle),  # 方位角（度）
            },

            # 位置状态
            'position_state': {
                'is_above': z > 0,  # 是否在标记上方
                'is_centered': horizontal_distance < 0.5,  # 是否居中
                'is_landing_zone': z < 2.0,  # 是否在降落区域内
            }
        }

        return pose_info

    def _rotation_matrix_to_euler_angles(self, R):
        """
        将旋转矩阵转换为欧拉角（roll, pitch, yaw）
        """
        sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

        singular = sy < 1e-6

        if not singular:
            x = math.atan2(R[2, 1], R[2, 2])
            y = math.atan2(-R[2, 0], sy)
            z = math.atan2(R[1, 0], R[0, 0])
        else:
            x = math.atan2(-R[1, 2], R[1, 1])
            y = math.atan2(-R[2, 0], sy)
            z = 0

        return [math.degrees(x), math.degrees(y), math.degrees(z)]

    def calculate_landing_commands(self, pose_info, target_height=0.2):
        """
        根据位姿信息计算降落控制指令

        参数:
            pose_info: 位姿信息字典
            target_height: 目标高度（米）

        返回:
            commands: 控制指令字典
        """
        if pose_info is None:
            return None

        x = pose_info['translation']['x']
        y = pose_info['translation']['y']
        z = pose_info['translation']['z']

        # 控制指令
        commands = {
            'vertical': 0.0,  # 垂直速度（m/s）
            'lateral': 0.0,  # 横向速度（m/s）
            'forward': 0.0,  # 纵向速度（m/s）
            'yaw': 0.0,  # 偏航速度（rad/s）
            'throttle': 0.0,  # 油门
            'landing_phase': 0  # 降落阶段
        }

        # 计算目标高度
        height_error = z - target_height

        # 控制参数
        Kp_vertical = 0.5  # 垂直控制增益
        Kp_horizontal = 0.3  # 水平控制增益

        # 阶段1：高度控制
        if height_error > 1.0:  # 高度误差大于1米
            commands['vertical'] = -Kp_vertical * height_error
            commands['landing_phase'] = 1
        # 阶段2：水平对齐
        elif pose_info['distances']['horizontal'] > 0.1:  # 水平误差大于0.1米
            commands['lateral'] = -Kp_horizontal * x
            commands['forward'] = -Kp_horizontal * y
            commands['landing_phase'] = 2
        # 阶段3：精准降落
        else:
            commands['vertical'] = -0.2  # 缓慢下降
            commands['landing_phase'] = 3

            if height_error < 0.05:  # 非常接近地面
                commands['vertical'] = 0.0
                commands['throttle'] = 0.0
                commands['landing_phase'] = 4  # 完成降落

        return commands