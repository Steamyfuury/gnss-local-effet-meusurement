import numpy as np
from sklearn.metrics import pairwise_distances
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from tqdm import tqdm


from utils.nav_parser import parse_nav_file
from utils.pos_file_converter import parse_positions
from utils.parserRinex import obsToDataframeFinal
from utils.satelite_manager import get_satelites
from TDCP_3 import TDCP



# ftp://cddis.gsfc.nasa.gov/pub/gps/products/wwww/igswwwwd.sp3.Z | template ephemeris

class Doppler:
    """ 
    This Class is aimed to compute the receiver velocity from the Doppler effect 
    """
    def __init__(self):
        # set the good t_data ( 26 nov à 10:00:00 )
        self.sats = parse_nav_file("test_data/autoroute_plus_tunnel.nav")


    def get_k(self, D_i, f_ti, v_i, a_i, clock_drift, obs_err):
        c = 3.00*10**8
        res =  (c * (D_i / f_ti)) + np.vdot(v_i, a_i)
        
        # print(res - obs_err)


        return res


    def visualize(self, ru:np.ndarray, sats:list, t:int):
        """This function aimed to get a visualisation from the satelite data
        
        Arguments:
            ru {np.ndarray} -- The user position in the ECEF way
            sats {list} -- Satellites data which is used to compute satellites positions
            t {int} -- Time of computation, in gps time of week
        """

        indexes = [s.name for s in sats]

        positions = []
        for s in sats:
            x, y, z, vx, vy, vz = s.get_pos(t)
            positions.append([ x, y, z, vx, vy, vz])

        positions.append([ru[0], ru[1], ru[2], 0, 0, 0])
        indexes.append('usr')

        positions.append([0, 0, 0, 0, 0, 0])
        indexes.append("Orig")
        
        df = pd.DataFrame(np.array(positions), columns=['x','y','z', 'vx', 'vy', 'vz'], index=indexes)


        fig = plt.figure()
        ax = Axes3D(fig)

        for i in range( df.shape[0] ): #plot each point + it's index as text above
            x,y,z = df['x'][i], df['y'][i] , df['z'][i]
            vx, vy, vz = df['vx'][i]*3.6, df['vy'][i]*3.6 , df['vz'][i]*3.6

            ax.scatter(x, y, z, color='b') 
            ax.text( x, y, z,  '%s' % (str(indexes[i])), size=20, zorder=1,  
            color='k') 

            ax.quiver(x, y, z, vx, vy, vz  )

        plt.show()


    def get_available_satelites(self, t:int, sats:list, sats_obs:pd.DataFrame):
        """This function aimed to filter and return only the available satellites
        
        Arguments:
            t {int} -- time ine GPS week
            sats {list} -- Satelites data
            sats_obs {pd.DataFrame} -- The parsed RINEX data observation
        
        Returns:
            {list} -- a list of available satelites
        """
        obs_names = list(sats_obs.loc[2081, t].index)

        # print(obs_names)

        # print([s.name for s in sats])

        # print()

        # print(t)

        available_sats = list()
        min_toe = np.min([s.toe for s in sats])

        # print(min_toe)

        # exit()



        for s in sats:
            if(t <= s.toe + 2*60*60 and t >= s.toe and s.name in obs_names):
                available_sats.append(s)


        return available_sats


    def get_usr_velocity(self,t:int ,ru:np.ndarray, sats:list, sats_obs:pd.DataFrame, f_ti:list ):
        """Compute the receiver velocity
        
        Arguments:
            t {int} -- Time in GPS time of week
            ru {np.ndarray} -- receiver position in ECEF
            sats {list} -- list of available satelites, only the first three sats are taken
            sats_obs {pd.DataFrame} -- parsed observation file
            f_ti {list} -- The emited frequencie of the satellite
        
        Returns:
            float -- velocity in meter peer second
        """
        obs = sats_obs.loc[2081, t]

        D_i = np.array([obs.loc[s.name].doppler for s in sats[:3]])

        a1 = (sats[0].get_pos(t)[:3]*10**3 - ru)/(np.linalg.norm(sats[0].get_pos(t)[:3]*10**3 - ru))
        a2 = (sats[1].get_pos(t)[:3]*10**3 - ru)/(np.linalg.norm(sats[1].get_pos(t)[:3]*10**3 - ru))
        a3 = (sats[2].get_pos(t)[:3]*10**3 - ru)/(np.linalg.norm(sats[2].get_pos(t)[:3]*10**3 - ru))

        k1 = self.get_k(D_i[0], f_ti[0], np.array(sats[0].get_pos(t)[3:]), a1, sats[0].clock_drift, sats[0].observation_error )
        k2 = self.get_k(D_i[1], f_ti[1], np.array(sats[1].get_pos(t)[3:]), a2, sats[1].clock_drift, sats[1].observation_error )
        k3 = self.get_k(D_i[2], f_ti[2], np.array(sats[2].get_pos(t)[3:]), a3, sats[2].clock_drift, sats[2].observation_error )

        K = np.array([k1, k2, k3])

        M = np.array([a1, a2, a3])

        v = np.dot(np.linalg.inv(M), K)

        return np.linalg.norm(v)*3.6
    

    

    def draw_velocity_evolution(self, position_file_location:str, nav_file_location:str, obs_file_location:str ):
        """Compute, for all time in the position file location, the velocity with the doppler method
        
        Arguments:
            position_file_location {str} -- The position file location
            nav_file_location {str} -- The nav file location
            obs_file_location {str} -- The obs file location
        """
        
        sats = parse_nav_file(nav_file_location)

        # user_positions = parse_positions(position_file_location).set_index(["gps_sec_of_week"])

        # user_positions = user_positions.reset_index().drop_duplicates(subset ="gps_sec_of_week", inplace = False).set_index(["gps_sec_of_week"])

        # user_positions.to_hdf( position_file_location+'.hdf5', key='data')

        user_positions = pd.read_hdf(position_file_location + '.hdf5', 'data')

        # sats_observation = obsToDataframeFinal(obs_file_location)   

        # sats_observation.to_hdf(obs_file_location + '.hdf5', key='data')

        sats_observation = pd.read_hdf(obs_file_location + '.hdf5', 'data')

        # print(user_positions.head())

        # print(sats_observation.head())

        # Merge dataframes with the GPS_time_of_week indexes

        sats_observation = sats_observation.reset_index().rename(columns={"second_of_week":'gps_sec_of_week'}).set_index(['gps_sec_of_week'])

        user_positions = user_positions.merge(sats_observation, left_index=True, right_index=True).reset_index().set_index(['n_week','gps_sec_of_week', 'name']) 

        time = list(user_positions.index.get_level_values(1))

        vs = list()
        doppler_v2 = list()
        true_velocity = list()
        time_vel= list()

        for t in tqdm(time) : 
            tmp_sats = self.get_available_satelites(t, sats, user_positions)
            
            ru = [user_positions.loc[2081,int(t)].iloc[0].x, user_positions.loc[2081,int(t)].iloc[0].y, user_positions.loc[2081,int(t)].iloc[0].z ]         
                
            if len(tmp_sats) >= 5: 

                tmp_sats = self.best_satelites(t, tmp_sats, ru)
            else:
                continue

            if len(tmp_sats) < 5:
                continue


            vs.append(np.linalg.norm(self.speed_for_the_win(t, ru, tmp_sats, user_positions)))
            doppler_v2.append(np.linalg.norm( self.get_usr_velocity(t,ru, tmp_sats, user_positions, [1.57542*10**9]*3 ) ))

            try:
                true_velocity.append(np.linalg.norm([ru -user_positions.loc[t-1]]) * 3.6 )
            except Exception:
                if(len(true_velocity)>0):
                    true_velocity.append(true_velocity[-1])
                else:
                    true_velocity.append(0)
            

            time_vel.append(t)

        plt.plot(time_vel,vs, label="Doppler second version")
        plt.plot(time_vel, true_velocity, label="Position derivative")
        plt.plot(time_vel, doppler_v2, label='Doppler first version')

        plt.legend()
        plt.grid()
        plt.show()


    def draw_velocity_evolution_TDCP(self, position_file_location:str, nav_file_location:str, obs_file_location:str ):
        """Compute, for all time in the position file location, the velocity with the doppler method
        
        Arguments:
            position_file_location {str} -- The position file location
            nav_file_location {str} -- The nav file location
            obs_file_location {str} -- The obs file location
        """
        
        sats = parse_nav_file(nav_file_location)

        # user_positions = parse_positions(position_file_location).set_index(["gps_sec_of_week"])

        # user_positions = user_positions.reset_index().drop_duplicates(subset ="gps_sec_of_week", inplace = False).set_index(["gps_sec_of_week"])

        # user_positions.to_hdf( position_file_location+'.hdf5', key='data')

        user_positions = pd.read_hdf(position_file_location + '.hdf5', 'data')

        # sats_observation = obsToDataframeFinal(obs_file_location)   

        # sats_observation.to_hdf(obs_file_location + '.hdf5', key='data')

        sats_observation = pd.read_hdf(obs_file_location + '.hdf5', 'data')

        sats_observation = sats_observation.reset_index().rename(columns={"second_of_week":'gps_sec_of_week'}).set_index(['gps_sec_of_week'])

        user_positions = user_positions.merge(sats_observation, left_index=True, right_index=True).reset_index().set_index(['n_week','gps_sec_of_week', 'name'])        

        time = list(user_positions.index.get_level_values(1))

        vs = list()
        true_velocity = list()
        time_vel= list()

        for t in tqdm(time) : 
            tmp_sats = self.get_available_satelites(t, sats, sats_observation)
            x_sk = np.array([[tmp_sats[i].get_pos(t) for i in range(4)],[tmp_sats[i+4].get_pos(t) for i in range(4)]])
            print(x_sk)
            try:
                ru = user_positions.loc[int(t)]
            except Exception :
                continue
            

            if len(tmp_sats) < 3:
                continue
            
            if len(tmp_sats) > 3: 
                tmp_sats = self.best_satelites(t, tmp_sats, ru)
            else:
                continue


            # print(list(sats_observation.index.get_level_values(1)).index(t))
            # return
            # tdcp = TDCP()
            # tdcp.TDCP_matlab()
            vs.append(self.get_usr_velocity( t, ru, tmp_sats, sats_observation, [1.57542*10**9] * 3)) 

            # print(t, " " ,[t_s.name for t_s in tmp_sats[:3]])
            # print()

            try:
                true_velocity.append(np.linalg.norm([ru -user_positions.loc[t-1]]) * 3.6 )
            except Exception:
                true_velocity.append(true_velocity[-1])
            

            time_vel.append(t)

        plt.plot(time_vel,vs, label="Doppler")
        plt.plot(time_vel, true_velocity, label="Position derivative")

        plt.legend()
        plt.grid()
        plt.show()


    
        

    def best_satelites(self, t:int, sats:list, user_position:np.ndarray):

        if(len(sats) == 5):
            return sats     

        spheric_coordonate = np.array([s.point_satelite_angles(user_position, t) for s in sats])

        names = [s.name for s in sats]

        satelite_dataframe = pd.DataFrame(spheric_coordonate, columns=['r', 'phi', 'theta'], index=names).sort_values(['theta', 'phi'])

        best_names = list(satelite_dataframe.index)

        best_names = [ best_names[i] for i in range(0, len(best_names), 2 ) ]

        best_satelites = list(filter(lambda s: s.name in best_names, sats))

        return best_satelites
        

    def compute_di(self,pseudo_rage_rate:float, vi, ai):
        return -pseudo_rage_rate  + np.dot(vi, ai)


    def speed_for_the_win(self, t:float, user_position:np.ndarray, sats:list, observation_dataframe:pd.DataFrame):

        ai = [(sats[i].get_pos(t)[:3] - user_position) / (np.linalg.norm(sats[i].get_pos(t)[:3] - user_position)) for i in range(5) ]

        ai = np.array(ai)

        usr_sat_dist = np.array([np.linalg.norm( sats[i].get_pos(t)[:3] - user_position ) for i in range(5) ])

        di = np.array([ self.compute_di(observation_dataframe.loc[2081, t, sats[i].name].pseudo_range - usr_sat_dist[i], sats[i].get_pos(t)[3:], ai[i] ) for i in range(5)])

        W = np.array([[ ai[i][0], ai[i][1], ai[i][2], -3.00*10**8, -1 ] for i in range(5)])

        res = np.linalg.lstsq(W, di, rcond=-1)[0]

        return res


    def test_velocity(self):

        time_ = 208800
        
        # di = [-2408.521, -2594.214, -2687.413]


        # positions = parse_positions("test_data/autoroute_plus_tunnel.pos").set_index(["gps_sec_of_week"])

        # positions.to_hdf("positions.hdf5", key="data")

        positions = pd.read_hdf("test_data/autoroute_plus_tunnel.pos.hdf5", "data")

        # ru = np.array([4043547.78553915, 254207.686387644, 4909623.02474359])

        ru = np.array(positions.loc[time_])

        # sats_obs = obsToDataframeFinal("test_data/autoroute_plus_tunnel.obs")

        # sats_obs.to_hdf("test_data/satelites_observation.hdf5", key='data')

        sats_obs = pd.read_hdf("test_data/satelites_observation.hdf5", 'data')

        

        sats_obs = sats_obs.reset_index()

        sats_obs.second_of_week = sats_obs.second_of_week # - 26

        sats_obs =sats_obs.set_index(["n_week", "second_of_week", "name"])

        sats = self.get_available_satelites(time_, self.sats, sats_obs)

        sats = self.best_satelites(time_, sats, ru)

        # self.visualize(ru, sats,time_)

        v = self.speed_for_the_win(time_, ru, sats, sats_obs)

        print('v1', np.linalg.norm(v[:3]))

        print(v)
        
        self.draw_velocity_evolution('test_data/autoroute_plus_tunnel.pos', 
        'test_data/autoroute_plus_tunnel.nav', 
        'test_data/autoroute_plus_tunnel.obs')




if __name__ == "__main__":
    sats = parse_nav_file("test_data/autoroute_plus_tunnel.nav")

    doppler = Doppler() 

    doppler.test_velocity()

    # doppler = Doppler()
    # doppler.draw_velocity_evolution()
    # doppler.get_usr_velocity()







