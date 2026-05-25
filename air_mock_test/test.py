import cv2
import numpy as np


class ArchDetector:
    def __init__(self):
        # ====================== 核心参数（根据你的场景微调）======================
        # 紫色HSV范围（比赛拱门专用，已根据你的图片校准）
        self.lower_purple = np.array([100, 40, 40])  # 调小更宽容
        self.upper_purple = np.array([160, 255, 255])  # 调大更宽容

        # 拱门几何约束
        self.min_arch_area = 2000  # 最小拱门面积（像素）
        self.max_arch_area = 80000  # 最大拱门面积（像素）
        self.arch_aspect_ratio = (0.5, 2.0)  # 拱门高宽比范围

        # 调试模式（开启后显示每一步处理结果）
        self.debug_mode = True

    def color_segmentation(self, frame):
        """第一步：颜色分割，只保留紫色区域"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        purple_mask = cv2.inRange(hsv, self.lower_purple, self.upper_purple)

        # 形态学操作：去除噪点，连接断裂的紫色区域
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        purple_mask = cv2.morphologyEx(purple_mask, cv2.MORPH_CLOSE, kernel)
        purple_mask = cv2.morphologyEx(purple_mask, cv2.MORPH_OPEN, kernel)

        if self.debug_mode:
            cv2.imshow("1. 紫色区域掩码", purple_mask)

        return purple_mask

    def find_arch_candidates(self, purple_mask):
        """第二步：寻找所有可能的拱门候选轮廓"""
        contours, _ = cv2.findContours(purple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if self.min_arch_area < area < self.max_arch_area:
                # 获取最小外接矩形
                rect = cv2.minAreaRect(cnt)
                (x, y), (w, h), angle = rect
                aspect_ratio = max(w, h) / min(w, h)

                # 高宽比校验
                if self.arch_aspect_ratio[0] < aspect_ratio < self.arch_aspect_ratio[1]:
                    candidates.append({
                        "contour": cnt,
                        "center": (int(x), int(y)),
                        "width": int(w),
                        "height": int(h),
                        "angle": angle
                    })

        return candidates

    def verify_arch_shape(self, frame, candidate):
        """第三步：验证拱门形状（空心门框特征）"""
        # 创建候选区域掩码
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [candidate["contour"]], -1, 255, -1)

        # 计算轮廓的凸包
        hull = cv2.convexHull(candidate["contour"])
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(candidate["contour"])

        # 空心特征：轮廓面积 / 凸包面积 < 0.5（中间是空的）
        hollow_ratio = contour_area / hull_area if hull_area > 0 else 1.0

        if self.debug_mode:
            print(f"候选区域空心度: {hollow_ratio:.2f}")

        # 拱门是空心的，所以空心度应该比较小
        return hollow_ratio < 0.7

    def detect_arch(self, frame):
        """拱门检测主流程"""
        # 1. 颜色分割，提取紫色区域
        purple_mask = self.color_segmentation(frame)

        # 2. 寻找候选轮廓
        candidates = self.find_arch_candidates(purple_mask)

        if self.debug_mode:
            print(f"找到 {len(candidates)} 个紫色候选区域")

        # 3. 形状验证
        best_arch = None
        max_area = 0

        for candidate in candidates:
            if self.verify_arch_shape(frame, candidate):
                # 选择面积最大的那个作为目标拱门
                if cv2.contourArea(candidate["contour"]) > max_area:
                    max_area = cv2.contourArea(candidate["contour"])
                    best_arch = candidate

        return best_arch

    def visualize_result(self, frame, arch_info):
        """可视化检测结果"""
        if arch_info is None:
            cv2.putText(frame, "No Arch Detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return frame

        # 绘制拱门轮廓
        cv2.drawContours(frame, [arch_info["contour"]], -1, (0, 255, 0), 3)

        # 绘制中心点
        center = arch_info["center"]
        cv2.circle(frame, center, 8, (0, 0, 255), -1)

        # 标注信息
        text = f"Arch Center: {center}"
        cv2.putText(frame, text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return frame


# ------------------------------ 测试代码 ------------------------------
if __name__ == "__main__":
    detector = ArchDetector()

    # 测试模式：0-单张图片，1-视频/摄像头
    test_mode = 0

    if test_mode == 0:
        # 替换为你的图片路径
        image_path = "img_1.png"
        frame = cv2.imread(image_path)

        if frame is None:
            print(f"错误：无法读取图片 {image_path}")
            exit()

        # 检测拱门
        arch_info = detector.detect_arch(frame)

        if arch_info:
            print(f"检测到拱门！中心点: {arch_info['center']}")
        else:
            print("未检测到拱门")

        # 可视化结果
        result = detector.visualize_result(frame, arch_info)
        cv2.imshow("最终检测结果", result)

        cv2.waitKey(0)
        cv2.destroyAllWindows()

    else:
        cap = cv2.VideoCapture(0)  # 或替换为视频路径

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            arch_info = detector.detect_arch(frame)
            result = detector.visualize_result(frame, arch_info)

            cv2.imshow("实时检测", result)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()