import matplotlib as mpl
import matplotlib .pyplot as plt
import numpy as np
import my_modules .my_tracing as debugging
import my_modules .my_io as io
import my_modules .process_stats_modules as ps_mod


class PlotModule :
    def __init__ (self, name, bar_width = 1.2) :
        self .outdir = '/' .join (name .split ('/') [:-1])
        self .name = name .split ('/') [-1] .rstrip ('.debug') 
        self .bar_width = bar_width

        self .ho =None
        self .lb = None
        self .alpha = None
        self .beta = None
        self .enb_percentage_base = None
        self .numUEs = None

        self .initialize_plt ()

    def __enter__ (self) :
        debugging .log ("Enter PlotModule with", self .name)
        self .ho, self .lb, alpha, beta, enb_percentage_base, numUEs = self .name .split('_')
        self .alpha = float (alpha [1:])
        self .beta = int (beta [1:])
        self .enb_percentage_base = int (enb_percentage_base [1:])
        self .numUEs = int (numUEs [1:])
        return self

    def __exit__ (self, exception_type, exception_value, traceback):
        debugging .log ("Exit PlotModule:", self .name)
    
    @debugging .trace (level = 2)
    def set_plot_attributes (self, 
                                ylabel = '', xlabel = '', title = '', text = None,
                                xlim = None, ylim = None) :
        if ylabel :
            self .plt .ylabel (ylabel)
        if xlabel :
            plt .xlabel (xlabel)
        if title :
            self .plt .title (', ' .join (['$LB_{algo}$ = ' + self .lb .upper (), 
                                            #'$\\alpha$ = ' + str (self .alpha) + '%', 
                                            #'$\\beta$ = ' + str (self.beta), 
                                            '$HO_{algo}$ = ' + self .ho .upper ()]))
                                            #'$|U|$ = ' + str (self .numUEs)]))
                                            #'$|eNB_{participated}|$ = ' + str (self .enb_percentage_base)]))
        if bool (xlim) :
            self .plt .xlim (xlim)
        if bool (ylim) :
            self .plt .ylim (ylim)

    @debugging .trace (level = 1)
    def plot_finishing_configs (self):
        self .set_plot_attributes (ylabel = "Number of eNBs", 
                                        xlabel = "Time (Seconds)", 
                                        title = False, 
                                        #xlim = [32, 127],
                                        ylim = [0,23])
        #self .plt .xticks (rotation = 'vertical')
        self .plt .gcf () .set_size_inches (14, 3.9) #report 4.6
        self .plt .legend (ncol = 3)
        self .plt .tight_layout ()

    @debugging .trace (level = 1)
    def initialize_plt (self) :
        self .plt = plt
        font = {'size' : 16}
        plt .rc ('font', **font)
        #plt .rc ('text', usetex = True)
        #mpl .rcParams ['text.latex.unicode'] = True


    @debugging .trace (level = 1)
    def plot_bar (self, fname):
        with ps_mod .ProcessStatsModule (fname .strip ('.debug')) as psm :
            x_vals, y_vals = psm .parse_lba_before ()
            self .plt .bar (x_vals, y_vals, self .bar_width, color = 'blue', label = 'Before Applying LBA ')
            x_vals, y_vals = psm .parse_lba_after ()
            self .plt .bar (x_vals + self .bar_width, y_vals, self .bar_width, color = 'green', label = 'After Applying LBA')

            self .plt .xticks (np .array (x_vals) + self .bar_width / 2, (str (i) for i in x_vals))
            self .plot_finishing_configs ()

    @debugging .trace (level = 1)
    def plot_bar_with_noLBAcase (self, fname, no_LBA_fname):
        with ps_mod .ProcessStatsModule (fname .strip('.debug')) as psm, ps_mod .ProcessStatsModule (no_LBA_fname .strip('.debug')) as psm_no_LBA:
            total_bars = 3
            bar_position = lambda bar_rank : (self .bar_width * ((-total_bars / 2) + (bar_rank - 1)))
            
            # no LBA
            x_vals, y_vals_high_load_enb, y_vals_enb_in_use = psm_no_LBA .parse_lba_before ()

            #in-use
            self .plt .bar (x_vals + bar_position (1), y_vals_enb_in_use, 
                            self .bar_width, color = 'green', edgecolor = 'black', label = self .ho .upper () + " (load > 0)")#label = 'Without LBA (load $\\geq 0$)')#, hatch = 'xx'
            #high-load
            self .plt .bar (x_vals + bar_position (2), y_vals_high_load_enb, 
                            self .bar_width, color = 'blue', edgecolor = 'black', label = self .ho .upper () + " (load $>\\beta$)")#'Without LBA (load $\\geq\\beta$)')

            # before LBA
            #x_vals, y_vals_high_load_enb, y_vals_enb_in_use = psm .parse_lba_before ()
            #self .plt .bar (x_vals + bar_position (3), y_vals_high_load_enb, 
            #                self .bar_width, color = 'blue', edgecolor = 'black', label = 'Before Applying LBA (load $\\geq \\beta$)')
            #self .plt .bar (x_vals + self .bar_width * 0, y_vals_enb_in_use, 
            #                self .bar_width, color = 'blue', edgecolor = 'black', hatch = 'xx', label = 'Before Applying LBA (total in use)')
            
            # after LBA
            x_vals, y_vals_high_load_enb, y_vals_enb_in_use = psm .parse_lba_after ()
            self .plt .bar (x_vals + bar_position (3), y_vals_high_load_enb, 
                            self .bar_width, color = 'red', edgecolor = 'black', label = self .ho .upper () + " + LB (load $>\\beta$))")#'With LBA (load $\\geq\\beta$)')
            #self .plt .bar (x_vals + self .bar_width * 2, y_vals_enb_in_use, 
            #                self .bar_width, color = 'green', edgecolor = 'black', hatch = 'xx', label = 'After Applying LBA (total in use)')

            # set tick names
            self .plt .xticks (np .array (x_vals) - self .bar_width / 2, (str (i) for i in x_vals))

            # alpha line
            #alpha_val = self .alpha * self .enb_percentage_base / 100 
            #alpha_vals = [alpha_val for _ in x_vals]
            #alpha_vals = psm_no_LBA .get_alpha_vals (self .alpha, x_vals)
            #self .plt .plot (x_vals, alpha_vals, color = 'r', ls = '-.', label = '$\\alpha=$' + str (self .alpha) + '%')

            self .plot_finishing_configs ()

    @debugging .trace (level = 1)
    def plot_curve_with_noLBAcase (self, fname, no_LBA_fname):
        with ps_mod .ProcessStatsModule (fname .strip('.debug')) as psm, ps_mod .ProcessStatsModule (no_LBA_fname .strip('.debug')) as psm_no_LBA:
            # no LBA
            x_vals, y_vals_high_load_enb, y_vals_enb_in_use = psm_no_LBA .parse_lba_before ()

            if self .ho == "a3":
                self .ho = "a3rsrp"
            elif self .ho == "a2a4":
                self .ho = "a2a4rsrq"
            #in-use
            self .plt .plot (x_vals, y_vals_enb_in_use, 
                            color = 'green', ls = "-.", label = self .ho .upper () + " (load > 0)")
            #high-load
            self .plt .plot (x_vals, y_vals_high_load_enb, 
                            color = 'blue', ls = "--", label = self .ho .upper () + " (load $>\\beta$)")

            # after LBA
            x_vals, y_vals_high_load_enb, y_vals_enb_in_use = psm .parse_lba_after ()
            #self .plt .plot (x_vals, y_vals_enb_in_use, 
            #                color = 'black', label = self .ho .upper () + " + LB (load > 0))")

            self .plt .plot (x_vals, y_vals_high_load_enb, 
                            color = 'red', ls = "-", label = self .ho .upper () + " + LB (load $>\\beta$)")

            self .plot_finishing_configs ()

    @debugging .trace (level = 1)
    def plot_curve_with_noLBAcase2 (self, fname10, fname20, no_LBA_fname):
        with ps_mod .ProcessStatsModule (fname10 .strip('.debug')) as psm10, ps_mod .ProcessStatsModule (fname20 .strip('.debug')) as psm20, ps_mod .ProcessStatsModule (no_LBA_fname .strip('.debug')) as psm_no_LBA:
            # no LBA
            x_vals, y_vals_high_load_enb, y_vals_enb_in_use = psm_no_LBA .parse_lba_before ()

            #in-use
            self .plt .plot (x_vals, y_vals_enb_in_use, 
                            color = 'green', ls = "-", label = self .ho .upper () + " (load > 0)")
            #high-load
            self .plt .plot (x_vals, y_vals_high_load_enb, 
                            color = 'blue', ls = "-.", label = self .ho .upper () + " (load $>\\beta$)")

            # after LBA
            x_vals, y_vals_high_load_enb, y_vals_enb_in_use = psm10 .parse_lba_after ()
            self .plt .plot (x_vals, y_vals_high_load_enb, 
                    color = 'magenta', ls = ":", label = self .ho .upper () + " + LB (load $>\\beta, \\alpha = 10\\%$)")

            x_vals, y_vals_high_load_enb, y_vals_enb_in_use = psm20 .parse_lba_after ()
            self .plt .plot (x_vals, y_vals_high_load_enb, 
                            color = 'red', ls = "--", label = self .ho .upper () + " + LB (load $>\\beta, \\alpha = 20\\%$)")

            self .plot_finishing_configs ()

    @debugging .trace (level = 1)
    def show (self): 
        self .plt .show ()

    @debugging .trace (level = 1)
    def save_as (self, fname = ''):
        if fname == '' :
            fname = self .name
            outfile = '/' .join ([self .outdir , fname .replace ('.', '-') + '.eps'])
        else :
            outfile = fname
        debugging .log ("saving file as", outfile)
        self .plt .savefig (outfile, dpi = 400)

    @debugging .trace (level = 1)
    def show_stats (self, fname):
        with ps_mod .ProcessStatsModule (fname .strip ('.debug')) as psm :
            ec, uc = psm .parse_connection ([40, 110])
            ho_max, ho_min, ho_avg = {}, {}, {}
            for t in ec :
                y = [len (ec [t] [e]) for e in ec [t]]
                if bool (y):
                    ho_max [t] = max (y)
                    ho_min [t] = min (y)
                    ho_avg [t] = round (sum (y) / len (y), 3)

            '''
            print ('ho_max', ho_max)
            v = ho_max .values()
            print ('max', max (v), 'min', min (v), 'avg', round (sum (v) / len (v), 3))
            print ('ho_min', ho_min)
            v = ho_min .values()
            print ('max', max (v), 'min', min (v), 'avg', round (sum (v) / len (v), 3))
            print ('ho_avg', ho_avg)
            v = ho_avg .values()
            print ('max', max (v), 'min', min (v), 'avg', round (sum (v) / len (v), 3))

            print ("Number of eNbs used on average per time instance between [40-110] time range")
            v =  [len (ec [t]. keys ())for t in ec]
            print ('max', max (v), 'min', min (v), 'avg', round (sum (v) / len (v), 3))

            print ("ue_handover_count", uc)
            v = uc .values()
            print ('max', max (v), 'min', min (v), 'avg', round (sum (v) / len (v), 3))

            lsrl = psm .parse_LSRL ()
            print ("LSRL stats")
            if bool (lsrl):
                v = [max (lsrl [ue] , key = lambda x: x[0]) [0] for ue in lsrl] #max LSRL seen per UE
                print ('max', max (v), 'min', min (v), 'avg', round (sum (v) / len (v), 3))
                print ("Percentage LSRL")
                v = [round (sum ([x * y for  x,y in lsrl [ue]]) / 108 * 100, 3) for ue in lsrl] #count of LSRL per UE
                print ('max', max (v), 'min', min (v), 'avg', round (sum (v) / len (v), 3))
            else :
                print ("no lsrl")
            '''




