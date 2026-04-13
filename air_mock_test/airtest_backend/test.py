import cv2
import cv2.aruco as aruco
import numpy as np

# 1. 创建检测器对象
detector = aruco.ArucoDetector(
    aruco.getPredefinedDictionary(aruco.DICT_6X6_250),
    aruco.DetectorParameters()
)

# 2. 读取图像
frame = cv2.imread("img_1.png")
if frame is None:
    print("无法读取图像文件 marker_image.png")
    exit()

# 3. 检测标记
corners, ids, rejected = detector.detectMarkers(frame)

# 4. 输出结果
if ids is not None:
    print(f"成功检测到 {len(ids)} 个标记：")
    for i, marker_id in enumerate(ids):
        print(f"  Marker {i + 1}: ID={marker_id[0]}")

    # 可选：在图像上绘制检测结果
    result_image = aruco.drawDetectedMarkers(frame.copy(), corners, ids)
    cv2.imshow("检测结果", result_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("未识别到任何 ArUco 标记")