import serial
import time
import os
from tkinter import *
from tkinter import font

PATH = os.path.dirname(r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev_2\led.py")
#PATH = r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev_2\led.py"

PORT = 'COM5'

class LED():
    
    def __init__(self):
        self.init_window = Tk()
        self.connect_led(PORT)

        # Specify font of labels and button's text
        global ft_label, ft_button
        ft_label = font.Font(family='Arial', size=12)
        ft_button = font.Font(size=15)

    def connect_led(self, port):
        print(f'initiating connection on LED...')
        self.serialcomm = serial.Serial(port = port, baudrate = 9600, timeout = 1)
        time.sleep(0.05)
        print(f'Connection established')
    
    def read(self):
        read_val = ''
        for i in range(10):
            read_val = self.serialcomm.readline().decode('ascii')
            time.sleep(0.1)
            if read_val != '':
                break
            elif i == 10:
                read_val = "Read timeout"
        return read_val

    def led_on(self):
        cmd = "4_on"
        self.serialcomm.write(cmd.encode())

    def led_off(self):
        cmd = "4_off"
        self.serialcomm.write(cmd.encode())

    def disconnect_relay(self):
        self.led_off()
        self.serialcomm.close()
        print('LED disconnected!')

    def set_init_window(self):
        os.chdir(f"{PATH}")
        # Set the title, icon, size of the initial window
        self.init_window.title("LED Control")
        self.init_window.geometry("400x320")

        for widget in self.init_window.winfo_children():
            widget.destroy()

        init_frame = LabelFrame(self.init_window, padx=50, pady=20, borderwidth=5)
        init_frame.grid(row=0, column=0, padx=20, pady=25)

        init_label_1 = Label(init_frame, text="LED Switch", pady=5, font=('Arial', 14))
        init_label_1.grid(row=0, column=0, columnspan=3, pady=10)

        global on_btn
        on_btn = Button(init_frame, text="ON", font=ft_button,\
                    padx=30, pady=30, border=5, borderwidth=4, command=self.led_on)
        off_btn = Button(init_frame, text="OFF", font=ft_button,\
                    padx=30, pady=30, border=5, borderwidth=4, command=self.led_off)
        exit_btn = Button(self.init_window, text="Exit", font=ft_button,\
                    padx=52, borderwidth=4, command=self.exit_gui)

        on_btn.grid(row=1, column=0, padx=10)
        off_btn.grid(row=1, column=1, padx=10)
        exit_btn.grid(row=2, column=0)

        self.init_window.mainloop()

    # def on_gui(self):
    #     on_btn.config(text='OFF', command=self.off_gui)
    #     self.led_on()

    # def off_gui(self):
    #     on_btn.config(text='ON', command=self.on_gui)
    #     self.led_off()

    def exit_gui(self):
        self.disconnect_relay()
        self.init_window.destroy()



if __name__ == "__main__":
    os.chdir(PATH)
    led = LED()
    led.set_init_window()
