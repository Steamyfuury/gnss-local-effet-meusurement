import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from utils.nav_parser import parse_nav_file

# ftp://cddis.gsfc.nasa.gov/pub/gps/products/wwww/igswwwwd.sp3.Z | template ephemeris

class Doppler:
    # Compute basic parameters at request time
    def __init__(self):
        sats = parse_nav_file("data/Very_Bad_Trip/Belgique/autoroute_plus_tunnel.nav")
        print([sat.name for sat in sats])

        self.ri1 = sats[10].get_position()
        self.ri2 = sats[9].get_position()
        self.ri3 = -sats[0].get_position()
        
        self.vi1 = sats[10].get_velocity()
        self.vi2 = sats[9].get_velocity()
        self.vi3 = -sats[0].get_velocity()
        
    def __get_K_n(self,f_ti,Di,ri,ru,vi):
        c = 299792458
        ai = self.get_line_of_sight(ri,ru)
        return (c*Di)/f_ti - np.inner(vi,ai)

    def get_line_of_sight(self,ri,ru):
        return (ri-ru)/np.linalg.norm(ri-ru)

    def get_usr_velocity(self):
        #G6 et G23 // 10 & 9
        ru = np.array([4043743.6490  ,  261011.8175 ,  4909156.8423])
        f_ti = 1575.42*10**6
        

        Di1 = 1319.955
        Di2 = -513.404
        Di3 = -2687.413


        k1 = self.__get_K_n(f_ti,Di1,self.ri1,ru,self.vi1)
        k2 = self.__get_K_n(f_ti,Di2,self.ri2,ru,self.vi2)
        k3 = self.__get_K_n(f_ti,Di3,self.ri3,ru,self.vi3)

        a1 = self.get_line_of_sight(self.ri1,ru)
        a2 = self.get_line_of_sight(self.ri2,ru)
        a3 = self.get_line_of_sight(self.ri3,ru)

        x = 0
        y = 0
        z = 0
        #print(x.shape,"||",a1.shape)
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        ax.quiver(x,y,z, a1, a2, a3,length=0.1, normalize=True)
        # ax.set_xlim([-1, 1])
        # ax.set_ylim([-1, 1])
        # ax.set_zlim([-1, 1])
        # plt.show()


        K = np.array([k1,k2,k3])
        X = np.array([a1,a2,a3])
        
        v = np.linalg.solve(X,K)

        print(v, "m/s")
        
        return v



if __name__ == "__main__":
    sats = parse_nav_file("data/Very_Bad_Trip/Belgique/autoroute_plus_tunnel.nav")
    # print(sats[1].name)
    # print(sats[1].get_position()/1000)
    # print(np.linalg.norm(sats[1].get_velocity())*3.6)
    # velocity = Doppler(208784,1574762406,1.28612756881,0.489020369661*10**-8,0.260362529662*10**-2,0.7931942133,0.622682273388*10**-5,0.1460313797*10**-5,0.515365547943*10**4,0.25971875*10**3,0.2853125*10**2,-0.204890966415*10**-7,0.577419996262*10**-7,0.108886242411*10,-0.815426822943*10**-8,0.963852456438,0.431089385164*10**-9)
    doppler = Doppler()
    doppler.get_usr_velocity()





