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
breakpoint_region_name = "gf-integration.breakpoints"


class RunGf2Command(sublime_plugin.ApplicationCommand):
    def run(self):
        launch_gf2()


class StopGf2Command(sublime_plugin.ApplicationCommand):
    def run(self):
        kill_gf2()


class ToggleBreakpointCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if view is not None:
            cursors_pos = view.sel()
            if len(cursors_pos) >= 1:
                cursor_pos = cursors_pos[0]
                line, _ = view.rowcol(cursor_pos.a)
                toggle_breakpoint(view, line + 1)


class RemoveAllBreakpointsCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if view is not None:
            view.add_regions(breakpoint_region_name, [], "region.redish", "dot")
        send_command_to_gf2("c d")


class CursorEventListener(sublime_plugin.EventListener):
    def on_text_command(self, view, cmd, args):
        result = None
        if cmd == "drag_select" and "event" in args:
            event = args["event"]
            breakpoint_line = get_breakpoint_line(view, event["x"], event["y"])
            if breakpoint_line is not None:
                toggle_breakpoint(view, breakpoint_line)
                result = (cmd, args)
        return result

    def on_post_text_command(self, view, command_name, args):
        handle_view_change(view)

    def on_post_window_command(self, window, command_name, args):
        handle_view_change(window.active_view())


def handle_view_change(view):

    if gf2_is_running() and not view.is_dirty() and view.file_name() is not None:

        cur_file = view.file_name()
        if (
            global_state["gf2_open_file"] is None
            or global_state["gf2_open_file"] != cur_file
        ):
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


def toggle_breakpoint(view, line):
    if not gf2_is_running():
        launch_gf2()

    if gf2_is_running():
        filename = view.file_name()

        if filename is not None:

            current_regions = view.get_regions(breakpoint_region_name)

            breakpoints = global_state["breakpoints"]

            if filename not in breakpoints:
                breakpoints[filename] = {}

            breakpoints = breakpoints[filename]
            point_line_start = view.text_point(line - 1, 0)
            region = sublime.Region(point_line_start, point_line_start)

            if line in breakpoints:
                breakpoints.pop(line)
                current_regions.remove(region)
                cmd = f"c clear {filename}:{line}"
            else:
                breakpoints[line] = True
                current_regions.append(region)
                cmd = f"c b {filename}:{line}"

            view.add_regions(breakpoint_region_name, current_regions, "region.redish", "dot")
            send_command_to_gf2(cmd)


def launch_gf2():
    kill_gf2()

    settings = sublime.load_settings(settings_filename)
    pipe_path = settings["pipe_path"]

    if os.path.exists(pipe_path):
        os.remove(pipe_path)

    gf2_cmd = settings["gf2_cmd"]

    try:
        gf_working_dir = settings["working_directory"]
        try:
            active_view = sublime.active_window().active_view()
            if active_view is not None:
                gf_working_dir = active_view.settings()[
                    "gf-integration.working_directory"
                ]
        except Exception:
            pass

        if os.path.exists(gf_working_dir):
            global_state["gf2_process"] = subprocess.Popen(
                [gf2_cmd], cwd=gf_working_dir
            )
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
            kill_gf2()
        else:
            handle_view_change(sublime.active_window().active_view())

    except Exception as error:
        sublime.error_message(f"Couldn't start gf2 (command: {gf2_cmd}): {error}")


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


def kill_gf2():
    if global_state["gf2_process"] is not None:
        global_state["gf2_process"].terminate()
    cleanup()


def cleanup():
    global_state["gf2_process"] = None
    global_state["gf2_open_file"] = None


def get_breakpoint_line(view, event_window_x, event_window_y):
    result = None
    cursor_ch = view.window_to_text((event_window_x, event_window_y))
    window_cursor = view.text_to_window(cursor_ch)
    if abs(window_cursor[1] - event_window_y) < view.line_height():
        if event_window_x - window_cursor[0] < -view.em_width():
            line, col = view.rowcol(cursor_ch)
            result = line + 1
    return result
