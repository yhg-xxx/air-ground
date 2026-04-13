import cv2
import cv2.aruco as aruco
import numpy as np
import time

# -------------------------- 配置参数（和你实时版保持一致） --------------------------
MARKER_LENGTH = 0.1  # 标记实际边长，单位：米（10cm）
COORDINATE_SYSTEM = 1  # 1: 中心坐标系, 0: 左上角坐标系
CAMERA_RESOLUTION = (1280, 720)  # 和你实时版的分辨率一致
IMAGE_PATH = "img_12.png"  # 替换成你的图片路径

# -------------------------- 相机内参（和实时版完全一致） --------------------------
width, height = CAMERA_RESOLUTION
camera_matrix = np.array([
    [width, 0, width / 2],
    [0, width, height / 2],
    [0, 0, 1]
], dtype=np.float32)
dist_coeffs = np.zeros((5, 1), dtype=np.float32)

# -------------------------- 创建检测器 --------------------------
dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(dictionary, parameters)


# -------------------------- 获取3D物体点（和实时版一致） --------------------------
def get_object_points(marker_length, coordinate_system=1):
    if coordinate_system == 1:
        # 中心坐标系
        half_size = marker_length / 2.0
        return np.array([
            [-half_size, half_size, 0],
            [half_size, half_size, 0],
            [half_size, -half_size, 0],
            [-half_size, -half_size, 0]
        ], dtype=np.float32)
    else:
        # 左上角坐标系
        return np.array([
            [0, 0, 0],
            [marker_length, 0, 0],
            [marker_length, marker_length, 0],
            [0, marker_length, 0]
        ], dtype=np.float32)


object_points = get_object_points(MARKER_LENGTH, COORDINATE_SYSTEM)

# -------------------------- 读取图像 --------------------------
frame = cv2.imread(IMAGE_PATH)
if frame is None:
    print(f"❌ 无法读取图像文件: {IMAGE_PATH}")
    print("请检查文件路径是否正确，文件名是否拼写正确")
    exit()

# 调整图像分辨率到和实时版一致（可选，保证内参匹配）
frame = cv2.resize(frame, CAMERA_RESOLUTION)
display_frame = frame.copy()

# -------------------------- 检测标记 --------------------------
corners, ids, rejected = detector.detectMarkers(frame)

if ids is not None and len(ids) > 0:
    print(f"✅ 成功检测到 {len(ids)} 个 ArUco 标记")

    # 绘制标记框
    display_frame = aruco.drawDetectedMarkers(display_frame, corners, ids)

    # 对每个标记做姿态估计
    for i in range(len(ids)):
        # 姿态估计
        success, rvec, tvec = cv2.solvePnP(
            object_points,
            corners[i],
            camera_matrix,
            dist_coeffs
        )

        if success:
            # 绘制坐标轴（和实时版一致）
            axis_length = MARKER_LENGTH * 0.5
            cv2.drawFrameAxes(
                display_frame,
                camera_matrix,
                dist_coeffs,
                rvec,
                tvec,
                axis_length,
                3
            )

            # 计算标记中心
            marker_corners = corners[i][0]
            center_x = int(np.mean(marker_corners[:, 0]))
            center_y = int(np.mean(marker_corners[:, 1]))

            # 绘制ID
            cv2.putText(
                display_frame,
                f"ID: {ids[i][0]}",
                (center_x - 40, center_y - 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            # 计算坐标和距离
            x_offset = tvec[0][0]
            y_offset = tvec[1][0]
            height = tvec[2][0]
            distance = np.linalg.norm(tvec)

            # 绘制X/Y/Z/Dist（黑边+白字，和实时版完全一致）
            # 黑色描边
            cv2.putText(display_frame, f"X: {x_offset:.2f}", (center_x - 40, center_y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            cv2.putText(display_frame, f"Y: {y_offset:.2f}", (center_x - 40, center_y + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            cv2.putText(display_frame, f"Z: {height:.2f}", (center_x - 40, center_y + 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            cv2.putText(display_frame, f"Dist: {distance:.2f}", (center_x - 40, center_y + 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            # 白色主体
            cv2.putText(display_frame, f"X: {x_offset:.2f}", (center_x - 40, center_y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(display_frame, f"Y: {y_offset:.2f}", (center_x - 40, center_y + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(display_frame, f"Z: {height:.2f}", (center_x - 40, center_y + 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(display_frame, f"Dist: {distance:.2f}", (center_x - 40, center_y + 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # 打印坐标信息
            print(f"\n📊 标记 ID {ids[i][0]} 姿态信息:")
            print(f"  X: {x_offset:.2f} m")
            print(f"  Y: {y_offset:.2f} m")
            print(f"  Z: {height:.2f} m")
            print(f"  距离: {distance:.2f} m")
else:
    print("❌ 未识别到任何 ArUco 标记")
    print("可能原因：")
    print("1. 图片中没有符合 DICT_6X6_250 的标记")
    print("2. 标记模糊、光照不足、角度过大")
    print("3. 标记尺寸和代码中 MARKER_LENGTH 不匹配")

# -------------------------- 显示和保存结果 --------------------------
# 显示结果
cv2.imshow("ArUco 单张识别结果", display_frame)
print("\n按任意键关闭窗口，按 S 保存图片")
key = cv2.waitKey(0) & 0xFF
if key == ord('s') or key == ord('S'):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    save_path = f"aruco_single_result_{timestamp}.jpg"
    cv2.imwrite(save_path, display_frame)
    print(f"✅ 结果已保存到: {save_path}")

cv2.destroyAllWindows()