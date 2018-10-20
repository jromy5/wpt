class Element(object):
    def __init__(self, session, remote_object_id):
        self._session = session
        self._remote_object_id = remote_object_id

    # In-view center point
    # https://w3c.github.io/webdriver/#dfn-center-point
    def in_view_center(self):
        inner_width, inner_height = self._session.execute_script(
            'return [innerWidth, innerHeight];'
        )
        quads = self._session._send('DOM.getBoxModel', {  # API status: stable
            'objectId': self._remote_object_id
        })['model']['border']

        left = max(0, min(quads[0], quads[2]))
        right = min(inner_width, max(quads[0], quads[2]))
        top = max(0, min(quads[1], quads[5]))
        bottom = min(inner_height, max(quads[1], quads[5]))

        return {
            'x': int((left + right) / 2),
            'y': int((top + bottom) / 2)
        }

    def click(self):
        center = self.in_view_center()
        self._session._send('Input.dispatchMouseEvent', {  # API status: stable
            'type': 'mouseMoved',
            'x': center['x'],
            'y': center['y']
        })
        self._session._send('Input.dispatchMouseEvent', {  # API status: stable
            'type': 'mousePressed',
            'button': 'left',
            'clickCount': 1,
            'x': center['x'],
            'y': center['y']
        })
        self._session._send('Input.dispatchMouseEvent', {  # API status: stable
            'type': 'mouseReleased',
            'button': 'left',
            'clickCount': 1,
            'x': center['x'],
            'y': center['y']
        })

    def _set_file(self, files):
        self._session._send('DOM.setFileInputFiles', {  # API status: stable
            'files': files,
            'objectId': self._remote_object_id,
        })

    def send_keys(self, text):
        is_file = self._session._send('Runtime.callFunctionOn', {  # API status: stable
            'functionDeclaration': '''
            function focus(target) {
              return target.nodeName.toLowerCase() === 'input' &&
                /^file$/.test(target.getAttribute('type'));
            }
            ''',
            'objectId': self._remote_object_id,
            'arguments': [{'objectId': self._remote_object_id}]
        })['result']['value']

        if is_file:
            return self._set_file(text.split('\n'))

        # Existing tests in WPT have been written to focus on the document
        # body. Because this is not a focusable element, the `DOM.focus` method
        # cannot be used. Instead, invoke the `focus` method, which has roughly
        # the same semantics as the relevant step in the WebDriver "Element
        # Send Keys" command.
        #
        # https://w3c.github.io/webdriver/#element-send-keys
        self._session._send('Runtime.callFunctionOn', {  # API status: stable
            'functionDeclaration': '''
            function focus(target) {
              if (target !== document.activeElement) {
                target.focus();
              }
            }
            ''',
            'objectId': self._remote_object_id,
            'arguments': [{'objectId': self._remote_object_id}]
        })

        for char in text:
            self._session._send('Input.dispatchKeyEvent', {  # API status: stable
                'type': 'keyDown',
                'text': char
            })
            self._session._send('Input.dispatchKeyEvent', {  # API status: stable
                'type': 'keyUp'
            })
