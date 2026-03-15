import socket
import threading
import json
import traceback
import customtkinter as ctk
from tkinter import messagebox
import hashlib

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

client,menu,menu_emoji,theme_menu = None,None,None,None

username = ""

EMOJI_FONT = ("Segoe UI Emoji", 16)

emoji_list = [
    "😀","😃","😄","😁","😆",
    "😂","🤣","😊","😍","😎",
    "🥰","😘","😜","🤔","😭",
    "👍","👏","🙏","🔥","❤️"
]

user_colors,messages,message_labels,message_owner = {},{},{},{}    

# generate user color
def get_color(name):
    h = hashlib.md5(name.encode()).hexdigest()
    return "#" + h[:6]

#หน้าต่าง LOGIN 
login = ctk.CTk()
login.title("Chatroom Meeting")
login.iconbitmap("chat.ico")

x = (login.winfo_screenwidth()//2-180)
y = (login.winfo_screenheight()//2-180)
login.geometry(f"360x300+{x}+{y}")

title = ctk.CTkLabel(login,text="Chatroom Meeting",font=("Arial",26,"bold"))
title.pack(pady=25)

username_entry = ctk.CTkEntry(login,placeholder_text="Username",width=220)
username_entry.pack(pady=8)

ip_entry = ctk.CTkEntry(login,placeholder_text="Server IP",width=220)
ip_entry.pack(pady=8)

port_entry = ctk.CTkEntry(login,placeholder_text="Port",width=220)
port_entry.insert(0,"5000")
port_entry.pack(pady=8)

# connect
def start_chat():

    global client,username

    username = username_entry.get()
    host = ip_entry.get()
    port = port_entry.get()

    if username=="" or host=="" or port=="":
        messagebox.showwarning("Error","กรูณากรอกข้อมูลให้ครบ")
        return

    try:
        port=int(port)
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect((host,port))

        # รอข้อความจาก server
        line = client.recv(1024).decode().strip()

        if line == "NAME":
            client.send(username.encode())

            # รอผลตรวจชื่อ
            response = client.recv(1024).decode().strip()

            if response == "NAME_TAKEN":
                messagebox.showerror("Error", "Username นี้มีคนใช้แล้ว")
                client.close()
                return
            elif response == "OK":
                login.destroy()
                open_chat()

    except Exception as e:
        print("Connection error:", e)
        messagebox.showerror("Error","Cannot connect to server")
        return

#หน้าต่าง Chatroom 
def open_chat():

    themes = {
        "Dark": {
            "room_bg": "#2b2b2b",
            "my_msg": "#2b6cb0",
            "other_msg": "#40444b"
        },
        "Midnight": {
            "room_bg": "#1e1f22",
            "my_msg": "#5865f2",
            "other_msg": "#313338"
        },
        "Purple": {
            "room_bg": "#2a1f3d",
            "my_msg": "#7c3aed",
            "other_msg": "#3b2a52"
        },
        "Ocean": {
            "room_bg": "#1e3a5f",
            "my_msg": "#0284c7",
            "other_msg": "#1f4a75"
        }
    }
    
    current_theme = themes["Dark"]

    root = ctk.CTk()
    root.title(f"Chatroom Meeting - {username}")
    root.iconbitmap("chat.ico")

    x = (root.winfo_screenwidth()//2-380)
    y = (root.winfo_screenheight()//2-300)
    root.geometry(f"760x560+{x}+{y}")

    # left panel
    left = ctk.CTkFrame(root,width=200)
    left.pack(side="left",fill="y",padx=5,pady=5)

    # right panel
    right = ctk.CTkFrame(root)
    right.pack(side="right",fill="both",expand=True,padx=5,pady=5)

    label = ctk.CTkLabel(left,text="ONLINE USERS",font=("Arial",16,"bold"))
    label.pack(pady=10)

    user_list = ctk.CTkTextbox(left,width=180,height=400,font=("Arial",13))
    user_list.pack(fill="both",expand=True,padx=8,pady=5)
    user_list.configure(state="disabled")

    btn_theme = ctk.CTkButton(left,text="CHANGE THEME",fg_color="#565B5E",hover_color="#404345",text_color="#DCE4EE",command=lambda: open_theme_menu())
    btn_theme.pack(fill="both",expand=True,padx=10,pady=20)

    # chat box
    chat_box = ctk.CTkScrollableFrame(right,fg_color=current_theme["room_bg"])
    chat_box.pack(fill="both",expand=True,padx=10,pady=10)
    
    typing_label = ctk.CTkLabel(right,text="")
    typing_label.pack()

    # input area
    input_frame = ctk.CTkFrame(right)
    input_frame.pack(fill="x",padx=10,pady=5)

    msg_entry = ctk.CTkEntry(input_frame,placeholder_text="Type a message...",font=("Segoe UI Emoji",14))
    msg_entry.pack(side="left",fill="x",expand=True,padx=5,pady=10)


    # functions
    def exit_chat():
        try:
            client.close()
        except:
            pass
        root.destroy()


    def send_msg(event=None):

        msg = msg_entry.get()

        if msg:
            client.send(msg.encode())
            msg_entry.delete(0,"end")


    def send_typing(event=None):

        try:
            client.send("__typing__".encode())
        except:
            pass

    def add_system(text):
        sys_frame = ctk.CTkFrame(chat_box, fg_color="transparent")
        sys_frame.pack(fill="x", pady=5)

        sys_label = ctk.CTkLabel(
            sys_frame,
            text=text,
            text_color="orange",
            font=("Segoe UI Emoji",12,"bold")
        )
        sys_label.pack(anchor="center")

    def add_chat(text,uid=None,msg_id=None):

        if ":" in text:

        # แยก timestamp
            if text.startswith("["):
                time_part = text.split("]")[0] + "]"
                rest = text.split("] ",1)[1]
            else:
                time_part = ""
                rest = text

            name,message = rest.split(":",1)
            name=name.strip()
            message=message.strip()

            key = uid if uid else name

            if key not in user_colors:
                user_colors[key] = get_color(key)

            if name == username: 
                bubble_bg = current_theme["my_msg"]   # สีข้อความของเรา
                anchor = "e"
                side_msg = ctk.RIGHT
            else: 
                bubble_bg = current_theme["other_msg"]   # สีข้อความคนอื่น
                anchor = "w"
                side_msg = ctk.LEFT

            msg_frame = ctk.CTkFrame(chat_box, fg_color="transparent")
            msg_frame.pack(fill="x", padx=5, pady=7.5, anchor=anchor)

            bubble_frame = ctk.CTkFrame(msg_frame, fg_color="transparent")
            bubble_frame.pack(fill="x", anchor=anchor)

            name_frame = ctk.CTkFrame(msg_frame, fg_color="transparent")
            name_frame.pack(fill="x", anchor=anchor)

            msg = ctk.CTkLabel(bubble_frame,text=message,fg_color=bubble_bg,font=("Segoe UI Emoji",14),corner_radius=15,padx=14,pady=8,wraplength=350,justify="left")
            time_label = ctk.CTkLabel(bubble_frame,text=time_part,text_color="#aaaaaa",font=("Segoe UI Emoji",12))
            name_label = ctk.CTkLabel(name_frame,text=name,text_color=user_colors[key],font=("Segoe UI Emoji",12,"bold"))

            msg.pack(side=side_msg, padx=10,pady=5,anchor="n")
            time_label.pack(side=side_msg, anchor="n")
            
            name_frame.pack(fill="x",padx=10,anchor=anchor)
            name_label.pack(side=side_msg)

            root.after(10, lambda: chat_box._parent_canvas.yview_moveto(1.0))

            if name == username:
                msg.bind("<Button-3>", lambda e, mid=msg_id,: open_message_menu(e, mid))

            if msg_id:
                messages[msg_id] = msg_frame
                message_labels[msg_id] = msg
                message_owner[msg_id] = name

        else:
            add_system(text)

    def edit_message(mid,new_text):
        if mid not in message_labels:
            return

        label = message_labels[mid]

        label.configure(text=new_text + " (แก้ไขแล้ว)")
    
    def send_delete(mid):

        client.send(json.dumps({
            "type":"delete",
            "id":mid
        }).encode())

    def delete_message(mid):

        if mid not in messages:
            return

        frame = messages[mid]
        frame.destroy()

        messages.pop(mid,None)
        message_labels.pop(mid,None)


    def open_message_menu(event, mid):

        global menu

        if menu and menu.winfo_exists():
            return
        
        text = message_labels[mid].cget("text")

        menu = ctk.CTkToplevel(root)
        menu.focus()
        menu.geometry(f"120x100+{event.x_root}+{event.y_root}")
        menu.overrideredirect(True)

        edit_btn = ctk.CTkButton(menu,text="Edit",corner_radius=15,command=lambda:(menu.destroy(),open_edit_dialog(mid,text)))
        edit_btn.pack(fill="x",padx=10,pady=7.5)

        del_btn = ctk.CTkButton(menu,text="Delete",fg_color="red",corner_radius=15,command=lambda:(menu.destroy(), send_delete(mid)))
        del_btn.pack(fill="x",padx=10,pady=7.5)

        menu.bind("<FocusOut>", lambda e: menu.destroy())
    
    def open_edit_dialog(mid, old_text):

        win = ctk.CTkToplevel(root)
        win.title("Edit Message")
        win.iconbitmap("chat.ico")

        x = (win.winfo_screenwidth()//2-150)
        y = (win.winfo_screenheight()//2-65)
        win.geometry(f"300x130+{x}+{y}")

        entry = ctk.CTkEntry(win,width=240)
        entry.insert(0,old_text)
        entry.pack(pady=20,padx=20)

        def save():
            new_text = entry.get()

            client.send(json.dumps({
                "type":"edit",
                "id":mid,
                "text":new_text
            }).encode())

            win.destroy()

        save_btn = ctk.CTkButton(win,text="Save",command=save)
        save_btn.pack(pady=10)
    
    def change_theme(theme_name):

        nonlocal current_theme

        current_theme = themes[theme_name]
        chat_box.configure(fg_color=current_theme["room_bg"])

        for mid,label in message_labels.items():

            owner = message_owner.get(mid)

            if owner == username:
                label.configure(fg_color=current_theme["my_msg"])
            else:
                label.configure(fg_color=current_theme["other_msg"])
    
    def open_theme_menu():

        global theme_menu

        if theme_menu and theme_menu.winfo_exists():
            return

        theme_menu = ctk.CTkToplevel(root)
        theme_menu.title("Theme")

        x = (theme_menu.winfo_screenwidth()//2-330)
        y = (theme_menu.winfo_screenheight()//2-100)
        theme_menu.geometry(f"180x170+{x}+{y}")

        theme_menu.grab_set()

        frame = ctk.CTkFrame(theme_menu)
        frame.pack(padx=5,pady=5)

        for t in themes:

            btn = ctk.CTkButton(
                frame,
                text=t,
                fg_color=themes[t]["room_bg"],      
                hover_color=themes[t]["my_msg"],
                corner_radius=10,
                command=lambda theme=t:(change_theme(theme), theme_menu.destroy())
            )
            btn.pack(fill="x",padx=5,pady=5)

    def update_users(users):
        user_list.configure(state="normal")
        user_list.delete("1.0","end")

        for user in users:

            name = user["name"]
            uid = user["uid"]

            if uid not in user_colors:
                user_colors[uid] = get_color(uid)

            color = user_colors[uid]

            user_list.tag_config(uid, foreground=color)
            user_list.insert("end", name + "\n", uid)

        user_list.configure(state="disabled")


    def reset_ui():
        
        for widget in chat_box.winfo_children():
            widget.destroy()
        add_system("[SYSTEM] Server ปิดแล้ว")

        user_list.configure(state="normal")
        user_list.delete("1.0","end")
        user_list.configure(state="disabled")

        user_colors.clear()

    # emoji picker
    def add_emoji(e):
        msg_entry.insert("end",e)

    def open_emoji():

        global menu_emoji

        if menu_emoji and menu_emoji.winfo_exists():
            return

        menu_emoji = ctk.CTkToplevel(root)
        menu_emoji.title("Emoji")
        menu_emoji.iconbitmap("chat.ico")
        x = (menu_emoji.winfo_screenwidth()//2-160)
        y = (menu_emoji.winfo_screenheight()//2-115)
        menu_emoji.geometry(f"320x230+{x}+{y}")

        menu_emoji.grab_set()  # ป้องกัน focus หลุด

        frame = ctk.CTkFrame(menu_emoji)
        frame.pack(padx=10,pady=10)

        row = 0
        col = 0

        for e in emoji_list:
            btn = ctk.CTkButton(
                frame,
                text=e,
                width=45,
                height=45,
                font=("Segoe UI Emoji",22),
                command=lambda emoji=e:(add_emoji(emoji), menu_emoji.destroy())
            )
            btn.grid(row=row,column=col,padx=4,pady=4)

            col += 1

            if col == 5:
                col = 0
                row += 1

    # receive thread
    def receive():

        buffer=""

        while True:
            try:
                data = client.recv(1024).decode()
                if not data:
                    root.after(0,reset_ui)
                    break
                buffer+=data

                while "\n" in buffer:

                    line,buffer = buffer.split("\n",1)

                    packet=json.loads(line)

                    if packet["type"]=="chat":
                        root.after(0,add_chat,packet["data"],packet.get("uid"),packet.get("id"))

                    elif packet["type"]=="system":
                        root.after(0,add_chat,"[SYSTEM] "+packet["data"])

                    elif packet["type"]=="users":
                        root.after(0,update_users,packet["data"])

                    elif packet["type"]=="history":
                        for m in packet["data"]:
                            root.after(0,add_chat,m["text"],m.get("uid"),m.get("id"))
                            root.after(1000, lambda: chat_box._parent_canvas.yview_moveto(1.0))

                    elif packet["type"]=="typing":
                        typing_label.configure(text=f"{packet['user']} is typing...")
                        root.after(2000,lambda: typing_label.configure(text=""))

                    elif packet["type"]=="edit":
                        root.after(0,edit_message,packet["id"],packet["text"])

                    elif packet["type"]=="delete":
                        root.after(0,delete_message,packet["id"])

            except (ConnectionResetError, ConnectionAbortedError):
                root.after(0, reset_ui)
                break
            except Exception as e:
                print("Receive error:", e)
                traceback.print_exc()
                root.after(0, reset_ui)
                break

    # buttons
    exit_btn = ctk.CTkButton(input_frame,text="Exit",fg_color="#963D3D",hover_color="#6F2E2E",width=70,command=exit_chat)
    exit_btn.pack(side="left",padx=5)

    emoji_btn = ctk.CTkButton(input_frame,text="😀",width=45,fg_color="transparent",font=("Segoe UI Emoji",23),command=open_emoji)
    emoji_btn.pack(side="left",padx=5)

    send_btn = ctk.CTkButton(input_frame,text="Send",width=80,fg_color="#3B8ED0",hover_color="#36719F",command=send_msg)
    send_btn.pack(side="right",padx=5)

    msg_entry.bind("<Return>",send_msg)
    msg_entry.bind("<Key>",send_typing)

    thread = threading.Thread(target=receive,daemon=True)
    thread.start()

    root.protocol("WM_DELETE_WINDOW",exit_chat)
    root.mainloop()

# connect button
connect_btn = ctk.CTkButton(login,text="Connect",width=180,command=start_chat)
connect_btn.pack(pady=25)

login.mainloop()

