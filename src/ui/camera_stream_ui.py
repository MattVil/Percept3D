import cv2
import time
import numpy as np
import ctypes

class CameraStreamUI:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index)
        self.prev_time = time.time()
        self.fps = 0
        self.selected_filter = None  # 'red', 'green', 'blue', or None
        self.header_height = 80
        self.button_width = 200  # Increased width for modern buttons
        self.button_height = 50
        self.button_margin = 30
        self.bg_color = (40, 40, 40)  # dark gray background

    def update_fps(self):
        """
        Update the frames per second (FPS) value based on the time elapsed since the last frame.
        """
        current_time = time.time()
        self.fps = 1 / (current_time - self.prev_time)
        self.prev_time = current_time

    def apply_filter(self, frame, color):
        """
        Apply a color filter (red, green, or blue) to the given frame.
        Args:
            frame (np.ndarray): The input image frame.
            color (str): The color filter to apply ('red', 'green', or 'blue').
        Returns:
            np.ndarray: The filtered image frame.
        """
        filtered = np.zeros_like(frame)
        if color == 'red':
            filtered[:, :, 2] = frame[:, :, 2]
        elif color == 'green':
            filtered[:, :, 1] = frame[:, :, 1]
        elif color == 'blue':
            filtered[:, :, 0] = frame[:, :, 0]
        return filtered

    def draw_header(self, panel, x, y, w, h):
        """
        Draw the header section at (x, y) with size (w, h), with modern styled buttons and updated UI colors.
        """
        header_panel = panel[y:y+h, x:x+w]
        # Draw "Percept3D" on the left
        cv2.putText(header_panel, "Percept3D", (self.button_margin, int(h * 0.65)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (220, 220, 220), 3)
        # Modern button design
        colors = [(60,60,220), (60,220,60), (220,60,60)]  # blue, green, red (muted)
        names = ['Red', 'Green', 'Blue']
        icons = [(36,36,255), (36,255,36), (255,36,36)]  # brighter for icon
        total_buttons_width = 3 * self.button_width + 2 * self.button_margin
        panel_width = w
        start_x = (panel_width - total_buttons_width) // 2
        y_btn = (h - self.button_height) // 2
        for i, (color, name, icon) in enumerate(zip(colors, names, icons)):
            x_btn = start_x + i * (self.button_width + self.button_margin)
            # Draw rounded rectangle (simulate by overlaying circles at corners)
            radius = 18
            btn_rect = (x_btn, y_btn, self.button_width, self.button_height)
            btn_color = color if self.selected_filter != name.lower() else tuple(min(255, c+60) for c in color)
            overlay = header_panel.copy()
            cv2.rectangle(overlay, (x_btn+radius, y_btn), (x_btn+self.button_width-radius, y_btn+self.button_height), btn_color, -1)
            cv2.rectangle(overlay, (x_btn, y_btn+radius), (x_btn+self.button_width, y_btn+self.button_height-radius), btn_color, -1)
            cv2.circle(overlay, (x_btn+radius, y_btn+radius), radius, btn_color, -1)
            cv2.circle(overlay, (x_btn+self.button_width-radius, y_btn+radius), radius, btn_color, -1)
            cv2.circle(overlay, (x_btn+radius, y_btn+self.button_height-radius), radius, btn_color, -1)
            cv2.circle(overlay, (x_btn+self.button_width-radius, y_btn+self.button_height-radius), radius, btn_color, -1)
            alpha = 0.92 if self.selected_filter != name.lower() else 1.0
            cv2.addWeighted(overlay, alpha, header_panel, 1-alpha, 0, header_panel)
            # Draw icon (filled circle)
            icon_center = (x_btn+30, y_btn+self.button_height//2)
            cv2.circle(header_panel, icon_center, 16, icon, -1)
            # Draw button text
            cv2.putText(header_panel, name, (x_btn+60, y_btn+36), cv2.FONT_HERSHEY_PLAIN, 2.1, (240,240,240), 2)
        # Draw FPS on the right side of the header
        fps_text = f"FPS: {self.fps:.2f}"
        (text_width, _), _ = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        cv2.putText(header_panel, fps_text, (panel_width - text_width - self.button_margin, int(h * 0.65)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (220,220,220), 2)

    def get_button_clicked(self, x, y, panel_width):
        """
        Determine which color filter button (if any) was clicked based on mouse coordinates.
        Args:
            x (int): The x-coordinate of the mouse click.
            y (int): The y-coordinate of the mouse click.
            panel_width (int): The width of the panel.
        Returns:
            str or None: The name of the button clicked ('red', 'green', 'blue'), or None if no button was clicked.
        """
        # Centered buttons
        total_buttons_width = 3 * self.button_width + 2 * self.button_margin
        start_x = (panel_width - total_buttons_width) // 2
        for i, name in enumerate(['red', 'green', 'blue']):
            bx = start_x + i * (self.button_width + self.button_margin)
            by = (self.header_height - self.button_height) // 2
            if bx <= x <= bx+self.button_width and by <= y <= by+self.button_height:
                return name
        return None

    def mouse_callback(self, event, x, y, flags, param):
        """
        Handle mouse click events to detect button presses in the header.
        Args:
            event: The OpenCV mouse event.
            x (int): The x-coordinate of the mouse event.
            y (int): The y-coordinate of the mouse event.
            flags: Any relevant flags passed by OpenCV.
            param (dict): Additional parameters, including panel width.
        """
        if event == cv2.EVENT_LBUTTONDOWN and y < self.header_height:
            panel_width = param['panel_width'] if param and 'panel_width' in param else 1920
            clicked = self.get_button_clicked(x, y, panel_width)
            if clicked:
                self.selected_filter = clicked

    def get_screen_resolution(self):
        """
        Get the screen resolution (width, height) of the primary monitor.
        Returns:
            tuple: (screen_width, screen_height)
        """
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    def draw_original_stream(self, panel, cam_frame, x, y, w, h, ratio=1.2):
        """
        Draw the original camera stream in the given rectangle, resizing and centering it to preserve aspect ratio.
        """
        xc, yc = x + w//2, y + h//2

        h_f, w_f = cam_frame.shape[:2]
        aspect = w_f / h_f

        display_w = int(w_f * ratio)
        display_h = int(display_w / aspect)

        resized = cv2.resize(cam_frame, (display_w, display_h))
        x1 = xc - display_w // 2
        y1 = yc - display_h // 2
        panel[y1:y1+display_h, x1:x1+display_w] = resized

        return x1, y1, display_h, display_w

    def draw_processed_stream(self, panel, cam_frame, x, y, w, h, ratio=1.2):
        """
        Draw the processed (filtered) camera stream in the given rectangle, resizing and centering it to preserve aspect ratio.
        """
        if self.selected_filter:
            proc_frame = self.apply_filter(cam_frame, self.selected_filter)
        else:
            proc_frame = cam_frame.copy()
        xc, yc = x + w//2, y + h//2

        h_f, w_f = proc_frame.shape[:2]
        aspect = w_f / h_f

        display_w = int(w_f * ratio)
        display_h = int(display_w / aspect)

        resized = cv2.resize(proc_frame, (display_w, display_h))
        x1 = xc - display_w // 2
        y1 = yc - display_h // 2
        panel[y1:y1+display_h, x1:x1+display_w] = resized

        return x1, y1, display_h, display_w

    def draw_footer(self, panel, x, y, w, h):
        """
        Draw the footer panel at (x, y) with size (w, h), with a modern color.
        """
        cv2.rectangle(panel, (x, y), (x+w, y+h), (30, 34, 40), -1)
        # Optionally, add text or info here

    def run(self):
        """
        Main loop to capture camera frames, process them, and display the interface with header, footer, and two stream panels.
        Handles user input for filter selection and quitting the application.
        """
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            return
        window_name = 'Percept3D'
        cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        ret, frame = self.cap.read()
        if not ret:
            print("Error: Failed to read frame.")
            return
        cam_h, cam_w, _ = frame.shape
        cam_aspect = cam_w / cam_h
        # Get screen size
        screen_w, screen_h = self.get_screen_resolution()
        # Compute panel heights
        header_height = int(0.10 * screen_h)
        footer_height = int(0.10 * screen_h)
        stream_panel_height = screen_h - header_height - footer_height
        stream_panel_width = screen_w // 2
        # Panel positions (x, y, w, h)
        header_rect = (0, 0, screen_w, header_height)
        footer_rect = (0, screen_h - footer_height, screen_w, footer_height)
        orig_rect = (0, header_height, stream_panel_width, stream_panel_height)
        proc_rect = (stream_panel_width, header_height, stream_panel_width, stream_panel_height)
        cv2.setMouseCallback(window_name, self.mouse_callback, param={'panel_width': screen_w})
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to read frame.")
                break
            self.update_fps()
            panel = np.full((screen_h, screen_w, 3), self.bg_color, dtype=np.uint8)
            # Draw header
            self.draw_header(panel, *header_rect)
            # Draw footer
            self.draw_footer(panel, *footer_rect)
            # Draw original stream
            _ = self.draw_original_stream(panel, frame, *orig_rect)
            # Draw processed stream
            _ = self.draw_processed_stream(panel, frame, *proc_rect)
            cv2.imshow(window_name, panel)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    ui = CameraStreamUI()
    ui.run()
