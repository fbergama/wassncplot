from vispy import gloo
from vispy import app
from vispy.gloo.util import _screenshot
from vispy.gloo.wrappers import read_pixels
import cv2 as cv
import numpy as np


vertex = """
        attribute vec2 position;
        attribute float elevation;
        varying vec4 fcolor;
        uniform float zmin;
        uniform float zmax;
        uniform float zalpha;
        uniform float rendermode;
        uniform mat4 P;

        // See: https://github.com/glumpy/glumpy/blob/master/glumpy/library/colormaps/jet.glsl
        vec3 colormap_jet(float t)
        {
            vec3 a, b;
            float c;
            if (t < 0.34) {
                a = vec3(0, 0, 0.5);
                b = vec3(0, 0.8, 0.95);
                c = (t - 0.0) / (0.34 - 0.0);
            } else if (t < 0.64) {
                a = vec3(0, 0.8, 0.95);
                b = vec3(0.85, 1, 0.04);
                c = (t - 0.34) / (0.64 - 0.34);
            } else if (t < 0.89) {
                a = vec3(0.85, 1, 0.04);
                b = vec3(0.96, 0.7, 0);
                c = (t - 0.64) / (0.89 - 0.64);
            } else {
                a = vec3(0.96, 0.7, 0);
                b = vec3(0.5, 0, 0);
                c = (t - 0.89) / (1.0 - 0.89);
            }
            return mix(a, b, c);
        }

        void main()
        {
            float far = 10000;
            float near = 10;
            float zr = (elevation-zmin)/(zmax-zmin);
            fcolor = rendermode * vec4( colormap_jet(zr), zalpha ) +
                     (1-rendermode) * vec4( position.x, position.y, elevation, 1.0 );

            vec4 paux = P*vec4(position.x, position.y, elevation, 1.0);
            gl_Position = vec4(paux.x / paux.z, -( paux.y/paux.z), 2.0*(paux.z-near)/(far-near)-1, 1.0);
        } """

fragment = """
           varying vec4 fcolor;
           void main() {
               gl_FragColor = fcolor;
           } """

vertex_bg = """
    attribute vec2 position;
    attribute vec2 texcoord;
    varying vec2 v_texcoord;
    void main()
    {
        gl_Position = vec4(position, 0.0, 1.0);
        v_texcoord = texcoord;
    }
"""

fragment_bg = """
    uniform sampler2D texture;
    varying vec2 v_texcoord;
    void main()
    {
        gl_FragColor = texture2D(texture, v_texcoord);
    }
"""


def gen_line_indices( M, N ):
    kk = np.asarray( range(0,(M-1)*N) ).reshape(M-1,N)

    kk1 = kk[:,0:-1]
    kk1 = kk1.reshape( kk1.size )
    kk2 = kk1+1
    kk4 = kk1+N+1
    
    kk123 = np.concatenate( (np.expand_dims(kk1,axis=1), 
                             np.expand_dims(kk2,axis=1), 
                             np.expand_dims(kk2,axis=1), 
                             np.expand_dims(kk4,axis=1)), axis=1 )
    return kk123.flatten()


def gen_triang_indices( M, N ):
    kk = np.asarray( range(0,(M-1)*N) ).reshape(M-1,N)

    kk1 = kk[:,0:-1]
    kk1 = kk1.reshape( kk1.size )
    kk2 = kk1+1
    kk3 = kk1+N
    kk4 = kk1+N+1
    
    kk123 = np.concatenate( (np.expand_dims(kk1,axis=1), 
                             np.expand_dims(kk2,axis=1), 
                             np.expand_dims(kk4,axis=1), 
                             np.expand_dims(kk1,axis=1),
                             np.expand_dims(kk4,axis=1),
                             np.expand_dims(kk3,axis=1)
                             ), axis=1 )

    return kk123.flatten()


class WaveView(app.Canvas):

    def __init__(self, title, width=800, height=600, wireframe=False ):
        app.Canvas.__init__(self, resizable=False, size=(width, height), show=False)
        self.width = width
        self.height = height
        self.wireframe = wireframe

        self._rendertex = gloo.Texture2D(shape=self.size[::-1] + (4,), internalformat="rgba32f")

        self._fbo = gloo.FrameBuffer(self._rendertex,
                                     gloo.RenderBuffer(self.size[::-1]))
        self.quad_bg = gloo.Program(vertex_bg, fragment_bg, count=4)
        self.quad_bg['position'] = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
        self.quad_bg['texcoord'] = [(0, 1), (0, 0), (1, 1), (1, 0)]

        gloo.set_clear_color('white')
        self.update()


    def setup_field( self, XX, YY, P0 ):
        """
        Setup the elevation field
            :param self: 
            :param XX: X-coordinates grid (in meshgrid format) (type: np.float32)
            :param YY: Y-coordinates grid (in meshgrid format) (type: np.float32)
            :param P0: Projection matrix from aligned sea-plane to camera 
        """   
        self.M = XX.shape[0]
        self.N = XX.shape[1]

        self.index_buff_t = gloo.IndexBuffer( np.array( gen_triang_indices(self.M,self.N), dtype=np.uint32 ) )

        if self.wireframe:
            self.index_buff = gloo.IndexBuffer( np.array( gen_line_indices(self.M,self.N), dtype=np.uint32 ) )
        else:
            self.index_buff = self.index_buff_t
        

        XX = XX.reshape( (XX.size,1) ).astype( np.float32 )
        YY = YY.reshape( (YY.size,1) ).astype( np.float32 )

        self.grid = gloo.Program(vertex, fragment )
        self.grid["position"] = np.concatenate( (XX,YY), axis=1 )
        self.set_zrange( -1, 1 )
        self.grid["P"] = P0.reshape( (P0.size,1) ).astype(np.float32)
        self.grid["elevation"] = np.zeros( XX.size, dtype=np.float32 )


    def on_draw(self, event):
        """
        Automatically invoked when render() is called
            :param self: 
            :param event: 
        """   
        #gloo.set_state(clear_color='white', blend=True,
        #               blend_func=('src_alpha', 'one_minus_src_alpha'))

        with self._fbo:

            # Produce the elevation rendering image
            gloo.clear( color=True, depth=True )
            gloo.set_state(depth_test=False, blend=False )
            self.quad_bg.draw('triangle_strip')

            gloo.clear(color=False, depth=True)
            gloo.set_state(depth_test=True, blend=True, blend_func=('src_alpha', 'one_minus_src_alpha') )
            self.grid["rendermode"] = 1
            self.grid.draw( "lines" if self.wireframe else "triangles", self.index_buff )
            self._im_zimg = read_pixels( out_type=np.float32 )

            # Produce the xyz image
            gloo.clear( color=True, depth=True )
            gloo.set_state(depth_test=True, blend=False )
            self.grid["rendermode"] = 0
            self.grid.draw( "triangles", self.index_buff_t )
            self._im_xyzimg = read_pixels( out_type=np.float32 )



    def set_zrange( self, zmin, zmax, zalpha=0.8 ):
        self.grid["zmin"] = float(zmin)
        self.grid["zmax"] = float(zmax)
        self.grid["zalpha"] = float(zalpha)


    def render( self, image, elevations ):
        """
        Renders the elevation map and returns the produced image
            :param image: Background image
            :param elevations: Elevation map
        """
        self.quad_bg['texture'] = gloo.Texture2D(image)
        elevations = elevations.reshape( (elevations.size,1) ) # Reshape elevations to column array
        self.grid["elevation"] = np.squeeze(elevations).astype(np.float32)
        self.update()
        app.process_events()
        return self._im_zimg, self._im_xyzimg
        #return app.Canvas.render( self )


if __name__ == "__main__":
    """ Simple test case """
    wv = WaveView()
    import scipy.io as sio
    data = sio.loadmat('/home/fibe/projects/WAVES/realtime/pipeline/WaveFieldVisualize/testdata.mat')
    wv.setup_field( data["XX"], data["YY"], data["P0plane"] )

    I = cv.imread('/home/fibe/projects/wass/test/output_W07/000000_wd/undistorted/00000000.png')

    img = wv.render( I, data["z"] )
    cv.imwrite( "test.png", img )
    wv.set_zrange(-2,2,0.8)
    img = wv.render( I, data["z"]*2 )
    cv.imwrite( "test2.png", img )
