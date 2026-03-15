import socket
import threading
import json
import traceback
import customtkinter as ctk
import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Server")
app.geometry("300x150")

status_label = ctk.CTkLabel(
    app,
    text="สถานะ: ปิดเซิร์ฟเวอร์อยู่",
    font=("Arial", 18),
    text_color="red"
)
status_label.pack(pady=10)

host = "192.168.0.101"
port = 5000

clients = {}
lock = threading.Lock()

history = []

server = None
server_running = False

user_counter = 1
message_counter = 1


def log(msg):
    # print(msg)
    status_label.configure(text=msg)


def broadcast(msg):
    for c in list(clients.keys()):
        try:
            c.send((msg + "\n").encode())
        except Exception as e:
            print("broadcast Error",e)
            traceback.print_exc()  
            pass # ถ้า client หลุด ไม่ให้ server crash


def send_user_list():
    users = []
    for uid in clients.values():
        name = uid.split("#")[0]
        users.append({"name": name, "uid": uid})

    packet = json.dumps({
        "type": "users",
        "data": users
    })
    broadcast(packet)


def handle_client(conn):

    global message_counter

    uid = clients[conn]
    name = uid.split("#")[0]

    while server_running:

        try:

            msg = conn.recv(1024).decode()

            if not msg:
                break

            msg = msg.strip()

            # typing indicator
            if msg == "__typing__":
                broadcast(json.dumps({
                    "type": "typing",
                    "user": name
                }))
                continue

            try:
                packet = json.loads(msg)

                # edit message
                if packet["type"] == "edit":

                    mid = packet["id"]
                    new_msg = packet["text"]

                    for m in history:
                        if m["id"] == mid and m["uid"] == uid:
                            
                            time = m["time"]
                            new_text = f"[{time}] {name}: {new_msg}"

                            m["text"] = new_text

                            broadcast(json.dumps({
                                "type":"edit",
                                "id":mid,
                                "text":new_msg
                            }))

                    continue

                # delete message
                if packet["type"] == "delete":

                    mid = packet["id"]

                    for m in history:
                        if m["id"] == mid and m["uid"] == uid:

                            history.remove(m)
                            broadcast(json.dumps({
                                "type":"delete",
                                "id":mid
                            }))

                    continue
            except:
                pass

            time = datetime.datetime.now().strftime("%H:%M")

            text = f"[{time}] {name}: {msg}"

            message_id = message_counter
            message_counter += 1

            history.append({
                "id":message_id,
                "text": text,
                "uid":uid,
                "time":time
            })

            packet = json.dumps({
                "type":"chat",
                "data":text,
                "uid":uid,
                "id":message_id
            })

            broadcast(packet)

        except Exception as e:
            print("handle Error",e)
            traceback.print_exc()
            break  # หากเกิดข้อผิดพลาด ให้หยุด loop

    with lock:
        if conn in clients:
            del clients[conn]

    broadcast(json.dumps({
        "type": "system",
        "data": f"{name} left the chat"
    }))

    send_user_list()
    conn.close()


def server_loop():

    global server, user_counter

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()

    log("สถานะ: เซิร์ฟเวอร์กำลังทำงาน")

    while server_running:

        try:

            conn, addr = server.accept()

            conn.send("NAME\n".encode())
            name = conn.recv(1024).decode().strip()

            with lock:
                existing_names = [uid.split("#")[0] for uid in clients.values()]

            if name in existing_names:
                conn.send("NAME_TAKEN\n".encode())
                conn.close()
                continue
            else:
                conn.send("OK\n".encode())

            uid = f"{name}#{user_counter}"
            user_counter += 1

            with lock:
                clients[conn] = uid

            packet = json.dumps({
                "type": "history",
                "data": history
            })

            conn.send((packet + "\n").encode())

            broadcast(json.dumps({
                "type": "system",
                "data": f"{name} joined the chat"
            }))

            send_user_list()

            thread = threading.Thread(
                target=handle_client,
                args=(conn,),
                daemon=True
            )
            thread.start()

        except Exception as e:
            print("Serverr Error",e)
            traceback.print_exc()
            break  # หากเกิดข้อผิดพลาด ให้หยุด loop


def start_server():
    global server_running

    if server_running:
        return

    server_running = True
    threading.Thread(target=server_loop, daemon=True).start()

    status_label.configure(
        text="สถานะ: Server กำลังทำงานอยู่",
        text_color="lightgreen"
    )


def stop_server():
    global server_running, server, history

    server_running = False

    if server:
        server.close()

    history.clear()

    status_label.configure(
        text="สถานะ: ปิดเซิร์ฟเวอร์แล้ว",
        text_color="red"
    )


start_button = ctk.CTkButton(app, text="Start Server", command=start_server)
start_button.pack(pady=10)

stop_button = ctk.CTkButton(app, text="Stop Server", fg_color="red", command=stop_server)
stop_button.pack(pady=10)

app.mainloop()