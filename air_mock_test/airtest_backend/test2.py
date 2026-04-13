import cv2
import cv2.aruco as aruco
import numpy as np
import time


class RealTimeArUcoPoseDetector:
    def __init__(self, camera_id=0, marker_length=0.1, coordinate_system=1):
        """
        Initialize real-time ArUco pose detector
        """
        self.camera_id = camera_id
        self.marker_length = marker_length
        self.coordinate_system = coordinate_system

        # Display controls
        self.show_axes = True
        self.show_info = True
        self.show_fps = True
        self.show_controls = True

        # Initialize camera
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            print(f"Cannot open camera {camera_id}")
            return

        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Get actual resolution
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Camera intrinsic parameters (default values)
        self.camera_matrix = np.array([
            [self.width, 0, self.width / 2],
            [0, self.width, self.height / 2],
            [0, 0, 1]
        ], dtype=np.float32)

        self.dist_coeffs = np.zeros((5, 1))

        # Create detector
        dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
        parameters = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(dictionary, parameters)

        # Statistics
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_time = time.time()
        self.fps = 0

        print(f"Camera started: {self.width}x{self.height}")
        print(f"Camera matrix:\n{self.camera_matrix}")
        print(f"Coordinate system: {'Center' if coordinate_system == 1 else 'Top-left'}")

    def get_object_points(self):
        """Get 3D object points"""
        if self.coordinate_system == 1:
            # Center coordinate system
            half_size = self.marker_length / 2.0
            return np.array([
                [-half_size, half_size, 0],
                [half_size, half_size, 0],
                [half_size, -half_size, 0],
                [-half_size, -half_size, 0]
            ], dtype=np.float32)
        else:
            # Top-left coordinate system
            return np.array([
                [0, 0, 0],
                [self.marker_length, 0, 0],
                [self.marker_length, self.marker_length, 0],
                [0, self.marker_length, 0]
            ], dtype=np.float32)

    def detect_and_draw(self, frame):
        """Detect markers and draw results"""
        # Copy frame for drawing
        display_frame = frame.copy()

        # Detect ArUco markers
        corners, ids, rejected = self.detector.detectMarkers(frame)

        if ids is not None and len(ids) > 0:
            # Draw detected markers
            display_frame = aruco.drawDetectedMarkers(display_frame, corners, ids)

            # Estimate pose for each marker
            object_points = self.get_object_points()

            for i in range(len(ids)):
                # Estimate pose using solvePnP
                success, rvec, tvec = cv2.solvePnP(
                    object_points,
                    corners[i],
                    self.camera_matrix,
                    self.dist_coeffs
                )

                if success:
                    # Draw coordinate axes
                    if self.show_axes:
                        axis_length = self.marker_length * 0.5
                        cv2.drawFrameAxes(
                            display_frame,
                            self.camera_matrix,
                            self.dist_coeffs,
                            rvec,
                            tvec,
                            axis_length,
                            3
                        )

                    # Show ID at marker center
                    marker_corners = corners[i][0]
                    center_x = int(np.mean(marker_corners[:, 0]))
                    center_y = int(np.mean(marker_corners[:, 1]))

                    # Draw ID
                    cv2.putText(
                        display_frame,
                        f"ID: {ids[i][0]}",
                        (center_x - 40, center_y - 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

                    # Show pose information
                    if self.show_info:
                        x_offset = tvec[0][0]
                        y_offset = tvec[1][0]
                        height = tvec[2][0]
                        distance = np.linalg.norm(tvec)

                        # 白色文字 + 黑色描边，超级清晰
                        # 描边
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

        return display_frame, len(ids) if ids is not None else 0

    def draw_info_panel(self, frame, markers_count):
        """Draw information panel"""
        display_frame = frame.copy()

        # Calculate FPS
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = current_time

        # Top-left information area
        y_offset = 30
        line_height = 25

        # Title
        if self.show_info:
            cv2.putText(
                display_frame,
                "ArUco Marker Detection",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )
            y_offset += line_height

            # Coordinate system info
            coord_system = "Center" if self.coordinate_system == 1 else "Top-left"
            cv2.putText(
                display_frame,
                f"Coords: {coord_system}",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
            y_offset += line_height

            # Detected markers count
            cv2.putText(
                display_frame,
                f"Markers: {markers_count}",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
            y_offset += line_height

            # Marker size
            cv2.putText(
                display_frame,
                f"Size: {self.marker_length * 100:.0f}cm",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
            y_offset += line_height

        # Top-right FPS display
        if self.show_fps:
            cv2.putText(
                display_frame,
                f"FPS: {self.fps}",
                (self.width - 100, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        # Bottom control hints
        if self.show_controls:
            controls = [
                "Controls:",
                "Q:Quit  S:Save  A:Toggle Axes  I:Toggle Info  F:Toggle FPS  C:Toggle Controls"
            ]

            for i, line in enumerate(controls):
                y_pos = self.height - 60 + i * 25
                cv2.putText(
                    display_frame,
                    line,
                    (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (200, 200, 200),
                    1
                )

        return display_frame

    def save_frame(self, frame):
        """Save current frame"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"aruco_snapshot_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        print(f"Saved: {filename}")

    def run(self):
        """Main run loop"""
        print("\n" + "=" * 50)
        print("Real-Time ArUco Marker Pose Detection")
        print("=" * 50)
        print("Controls:")
        print("  Q: Quit program")
        print("  S: Save current frame")
        print("  A: Toggle coordinate axes")
        print("  I: Toggle information display")
        print("  F: Toggle FPS display")
        print("  C: Show/hide control hints")
        print("=" * 50)

        try:
            while True:
                # Read frame
                ret, frame = self.cap.read()
                if not ret:
                    print("Cannot read frame")
                    break

                # Frame counter
                self.frame_count += 1

                # Detect markers
                processed_frame, markers_count = self.detect_and_draw(frame)

                # Draw information panel
                final_frame = self.draw_info_panel(processed_frame, markers_count)

                # Show result
                cv2.imshow("ArUco Marker Detection", final_frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print("Exiting program...")
                    break
                elif key == ord('s') or key == ord('S'):
                    self.save_frame(final_frame)
                elif key == ord('a') or key == ord('A'):
                    self.show_axes = not self.show_axes
                    status = "ON" if self.show_axes else "OFF"
                    print(f"Axes display: {status}")
                elif key == ord('i') or key == ord('I'):
                    self.show_info = not self.show_info
                    status = "ON" if self.show_info else "OFF"
                    print(f"Info display: {status}")
                elif key == ord('f') or key == ord('F'):
                    self.show_fps = not self.show_fps
                    status = "ON" if self.show_fps else "OFF"
                    print(f"FPS display: {status}")
                elif key == ord('c') or key == ord('C'):
                    self.show_controls = not self.show_controls
                    status = "SHOW" if self.show_controls else "HIDE"
                    print(f"Controls: {status}")

        except KeyboardInterrupt:
            print("\nProgram interrupted by user")
        except Exception as e:
            print(f"Program error: {e}")
        finally:
            # Release resources
            if hasattr(self, 'cap'):
                self.cap.release()
            cv2.destroyAllWindows()

            # Calculate and display statistics
            total_time = time.time() - self.start_time
            avg_fps = self.frame_count / total_time if total_time > 0 else 0

            print("\n" + "=" * 50)
            print("Program Statistics:")
            print(f"  Total runtime: {total_time:.1f}s")
            print(f"  Average FPS: {avg_fps:.1f}")
            print(f"  Final resolution: {self.width}x{self.height}")
            print("=" * 50)


# Simplified version for debugging
def simple_aruco_detection():
    """Simplified ArUco real-time detection"""

    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Create detector
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)

    # Camera parameters
    width = 640
    height = 480
    camera_matrix = np.array([
        [500, 0, width / 2],
        [0, 500, height / 2],
        [0, 0, 1]
    ], dtype=np.float32)

    dist_coeffs = np.zeros((5, 1))

    # Marker size
    marker_length = 0.1
    half_len = marker_length / 2.0

    # 3D points
    object_points = np.array([
        [-half_len, half_len, 0],
        [half_len, half_len, 0],
        [half_len, -half_len, 0],
        [-half_len, -half_len, 0]
    ], dtype=np.float32)

    print("ArUco detection started")
    print("Press 'q' to quit")
    print("Press 's' to save frame")

    frame_count = 0
    start_time = time.time()
    show_axes = True
    show_info = True

    while True:
        # Read frame
        ret, frame = cap.read()
        if not ret:
            print("Cannot read frame")
            break

        frame_count += 1

        # Detect markers
        corners, ids, rejected = detector.detectMarkers(frame)

        if ids is not None:
            # Draw markers
            frame = cv2.aruco.drawDetectedMarkers(frame, corners, ids)

            # Estimate pose
            for i, marker_id in enumerate(ids):
                marker_corners = corners[i][0]

                success, rvec, tvec = cv2.solvePnP(
                    object_points,
                    marker_corners,
                    camera_matrix,
                    dist_coeffs
                )

                if success and show_axes:
                    # Draw coordinate axes
                    frame = cv2.drawFrameAxes(
                        frame, camera_matrix, dist_coeffs,
                        rvec, tvec, marker_length * 0.3, 2
                    )

                    # Show ID
                    center_x = int(np.mean(marker_corners[:, 0]))
                    center_y = int(np.mean(marker_corners[:, 1]))
                    cv2.putText(frame, f"ID: {marker_id[0]}",
                                (center_x - 40, center_y - 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    if show_info:
                        x_offset = tvec[0][0]
                        y_offset = tvec[1][0]
                        height = tvec[2][0]
                        distance = np.linalg.norm(tvec)

                        # 黑边+白字
                        cv2.putText(frame, f"X: {x_offset:.2f}", (center_x - 40, center_y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                        cv2.putText(frame, f"Y: {y_offset:.2f}", (center_x - 40, center_y + 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                        cv2.putText(frame, f"Z: {height:.2f}", (center_x - 40, center_y + 40), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 0, 0), 2)
                        cv2.putText(frame, f"Dist: {distance:.2f}", (center_x - 40, center_y + 65),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

                        cv2.putText(frame, f"X: {x_offset:.2f}", (center_x - 40, center_y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(frame, f"Y: {y_offset:.2f}", (center_x - 40, center_y + 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(frame, f"Z: {height:.2f}", (center_x - 40, center_y + 40), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (255, 255, 255), 1)
                        cv2.putText(frame, f"Dist: {distance:.2f}", (center_x - 40, center_y + 65),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Calculate FPS
        current_time = time.time()
        fps = frame_count / (current_time - start_time)

        # Display information
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Frame: {frame_count}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Markers: {len(ids) if ids is not None else 0}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, "Q:Quit S:Save A:Axes I:Info", (10, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Show image
        cv2.imshow('ArUco Detection', frame)

        # Keyboard control
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"aruco_snapshot_{timestamp}.png"
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename}")
        elif key == ord('a'):
            show_axes = not show_axes
            print(f"Axes: {'SHOW' if show_axes else 'HIDE'}")
        elif key == ord('i'):
            show_info = not show_info
            print(f"Info: {'SHOW' if show_info else 'HIDE'}")

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    print(f"\nDetection finished, total frames: {frame_count}")


if __name__ == "__main__":
    # Method 1: Use full version
    try:
        detector = RealTimeArUcoPoseDetector(
            camera_id=0,
            marker_length=0.1,
            coordinate_system=1
        )

        detector.run()
    except Exception as e:
        print(f"Full version failed: {e}")
        print("\nTrying simplified version...")

        # Method 2: Use simplified version
        simple_aruco_detection()