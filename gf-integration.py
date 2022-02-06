import sublime
import sublime_plugin
import subprocess
import os
import time

global_state = {
	"gf2_process": None,
	"gf2_open_file": None,
	"breakpoints": {},
}

settings_filename = "gf-integration.sublime-settings"

class RunGf2Command(sublime_plugin.ApplicationCommand):

	def run(self):

		if global_state["gf2_process"] is not None:
			global_state["gf2_process"].terminate()
			cleanup()

		settings = sublime.load_settings(settings_filename)
		pipe_path = settings["pipe_path"]

		if os.path.exists(pipe_path):
			os.remove(pipe_path)

		gf2_cmd = settings["gf2_cmd"]

		try:
			project_gf_path = settings["project_gf_path"]
			try:
				project_gf_path = sublime.active_window().active_view().settings()["gf-integration.project_gf_path"]
			except Exception:
				pass

			if os.path.exists(project_gf_path):
				project_gf_base = os.path.dirname(project_gf_path)
				global_state["gf2_process"] = subprocess.Popen([gf2_cmd], cwd=project_gf_base)
			else:
				global_state["gf2_process"] = subprocess.Popen([gf2_cmd])

			sleep_inc = 0.1
			max_wait = 1
			waited = 0
			while not os.path.exists(pipe_path):
				time.sleep(sleep_inc)
				waited += sleep_inc
				if waited >= max_wait:
					break
			
			if not os.path.exists(pipe_path):
				sublime.error_message(f"gf launched but did not create pipe at {pipe_path}")
				global_state["gf2_process"].terminate()
				cleanup()
			else:
				handle_view_change(sublime.active_window().active_view())

		except Exception as error:
			sublime.error_message(f"Couldn't start gf2 (command: {gf2_cmd}): {error}")

class StopGf2Command(sublime_plugin.ApplicationCommand):

	def run(self):
		if global_state["gf2_process"] is not None:
			global_state["gf2_process"].terminate()
			cleanup()
		else:
			sublime.message_dialog("sublime-associated gf2 is not running")		

class ToggleBreakpointCommand(sublime_plugin.WindowCommand):

	def run(self):
		if gf2_is_running():
			view = self.window.active_view()
			cursors_pos = view.sel()
			
			if len(cursors_pos) >= 1:
				cursor_pos = cursors_pos[0]
				line, col = view.rowcol(cursor_pos.a)
				filename = view.file_name()

				if filename is not None:

					region_name = "gf-integration.breakpoints"
					current_regions = view.get_regions(region_name)

					breakpoints = global_state["breakpoints"]

					if filename not in breakpoints:
						breakpoints[filename] = {}

					breakpoints = breakpoints[filename]
					point_line_start = view.text_point(line, 0)
					region = sublime.Region(point_line_start, point_line_start)

					if line in breakpoints:
						breakpoints.pop(line)
						current_regions.remove(region)
						cmd = f"c clear {filename}:{line + 1}"
					else:
						breakpoints[line] = True
						current_regions.append(region)
						cmd = f"c b {filename}:{line + 1}"
					
					view.add_regions(region_name, current_regions, "region.redish", "dot")
					send_command_to_gf2(cmd)


class CursorEventListener(sublime_plugin.EventListener):

	def on_post_text_command(self, view, command_name, args):
		handle_view_change(view)

	def on_post_window_command(self, window, command_name, args):
		handle_view_change(window.active_view())


def handle_view_change(view):

	if gf2_is_running() and not view.is_dirty() and view.file_name() is not None:

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
				cmd = f"l {line + 1}"
				send_command_to_gf2(cmd)


def gf2_is_running():
	result = False
	if global_state["gf2_process"] is not None:
		result = True
		if global_state["gf2_process"].poll() is not None:
			result = False
			cleanup()
	return result


def send_command_to_gf2(cmd):
	pipe_path = sublime.load_settings(settings_filename)["pipe_path"]
	try:
		pipe_handle = os.open(pipe_path, os.O_WRONLY)
		os.write(pipe_handle, cmd.encode())
		os.close(pipe_handle)
	except Exception as error:
		print(f"could not send command {cmd} to pipe {pipe_path}: {error}")

def cleanup():
	global_state["gf2_process"] = None 
	global_state["gf2_open_file"] = None
