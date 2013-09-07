import anims
from pilight import eintr_wrap

commands = {}

def export (fn):
        commands[fn.__name__] = fn
        return fn

def unknown (sock, args, state):
        eintr_wrap (sock.send, b'500 Unknown command\r\n')

@export
def help (sock, args, state):
        eintr_wrap (sock.send, b'200 Known commands:\r\n200 {}\r\n'.format (' '.join (commands.keys ())))

@export
def set (sock, args, state):
        if len (args) != 3:
                eintr_wrap (sock.send, b'500 Usage: set {red|green|blue} {anim|speed|offset} VALUE\r\n')
                return

        colour = 'c_{}'.format (args[0])
        if colour not in state:
                eintr_wrap (sock.send, b'500 Bad colour\r\n')
                return
        colour = state[colour]

        if args[1] not in ['anim', 'speed', 'offset']:
                eintr_wrap (sock.send, b'500 Bad variable\r\n')
                return
        variable = args[1]

        if variable == 'anim':
                value = getattr (anims, args[2], None)
                if value is None:
                        eintr_wrap (socket.send, b'500 Bad animation\r\n')
                        return
        elif variable in ['anim', 'speed']:
                try:
                        value = float (args[2])
                except ValueError:
                        eintr_wrap (sock.send, b'500 Bad value\r\n')
                        return

        colour[variable] = value
        eintr_wrap (sock.send, b'200 Ok\r\n')
