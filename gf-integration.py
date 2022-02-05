import sublime
import sublime_plugin
import subprocess
import os

global_state = {
	"gf2_process": None, 
	"gf2_open_file": None,
	"pipe_path": "/home/sen/Projects/sublime-gf-integration/test-control-pipe.dat",
}

class RunGf2Command(sublime_plugin.ApplicationCommand):

	def run(self):
		if global_state["gf2_process"] is None:
			
			pipe_path = global_state["pipe_path"]
			if os.path.exists(pipe_path):
				os.remove(pipe_path)

			try:
				global_state["gf2_process"] = subprocess.Popen(["gf2"])
			except Exception:
				print("couldn't run gf2")

class CursorEventListner(sublime_plugin.EventListener):

	def on_post_text_command(self, view, command_name, args):
		handle_view_change(view)

	def on_post_window_command(self, window, command_name, args):
		handle_view_change(window.active_view())

def handle_view_change(view):

	if global_state["gf2_process"] is not None and global_state["gf2_process"].poll() is not None:
		global_state["gf2_process"] = None
		global_state["gf2_open_file"] = None

	if global_state["gf2_process"] is not None and not view.is_dirty() and view.file_name() is not None:

		cur_file = view.file_name()
		if global_state["gf2_open_file"] is None or global_state["gf2_open_file"] != cur_file:
			cmd = f"f {cur_file}"
			send_command_to_gf2(cmd)
			global_state["gf2_open_file"] = cur_file

		cursors_pos = view.sel()
		if len(cursors_pos) == 1:
			cursor_pos = cursors_pos[0]
			if cursor_pos.a == cursor_pos.b:
				line, col = view.rowcol(cursor_pos.a)
				pipe_path = global_state["pipe_path"]
				cmd = f"l {line + 1}"
				send_command_to_gf2(cmd)

def send_command_to_gf2(cmd):
	print(f"send command: {cmd}")
	try:
		pipe_path = global_state["pipe_path"]
		pipe_handle = os.open(pipe_path, os.O_WRONLY)
		os.write(pipe_handle, cmd.encode())
		os.close(pipe_handle)
	except Exception as error:
		print(f"could not send command {cmd} to pipe {pipe_path}: {error}")