from .base import Platform


__all__ = ['OSMesaPlatform']


class OSMesaPlatform(Platform):
    """Renders into a software buffer using OSMesa.
    Patched to use OSMesaCreateContextExt (Mesa 8 API) instead of
    OSMesaCreateContextAttribs (Mesa 21+ only) for compatibility with
    the libOSMesa.so.8 shipped on Debian/Ubuntu.
    """

    def __init__(self, viewport_width, viewport_height):
        super(OSMesaPlatform, self).__init__(viewport_width, viewport_height)
        self._context = None
        self._buffer = None

    def init_context(self):
        from OpenGL import arrays
        from OpenGL.osmesa import (
            OSMesaCreateContextExt,
            OSMESA_RGBA,
        )
        # depthBits=24, stencilBits=0, accumBits=0, sharelist=None
        self._context = OSMesaCreateContextExt(OSMESA_RGBA, 24, 0, 0, None)
        if not self._context:
            raise RuntimeError("OSMesaCreateContextExt failed — is libosmesa6 installed?")
        self._buffer = arrays.GLubyteArray.zeros(
            (self.viewport_height, self.viewport_width, 4)
        )

    def make_current(self):
        from OpenGL import GL as gl
        from OpenGL.osmesa import OSMesaMakeCurrent
        assert OSMesaMakeCurrent(
            self._context, self._buffer, gl.GL_UNSIGNED_BYTE,
            self.viewport_width, self.viewport_height
        )

    def make_uncurrent(self):
        pass

    def delete_context(self):
        from OpenGL.osmesa import OSMesaDestroyContext
        OSMesaDestroyContext(self._context)
        self._context = None
        self._buffer = None

    def supports_framebuffers(self):
        return False
