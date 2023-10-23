#!/snap/bin/pyroot

#/usr/bin/python3

# jk
# 20/09/2022
# 14.7.2023

#from __future__ import print_function

import ROOT
from math import sqrt, pow, log, exp
import os, sys, getopt

from labelTools import *

cans = []
stuff = []
lines = []


def makeLine(x1, x2, y1, y2):
    line = ROOT.TLine(x1, y1, x2, y2)
    line.SetLineColor(ROOT.kGreen)
    line.SetLineWidth(2)
    line.Draw()
    return line


def PrintUsage(argv):
    print('Usage:')
    print('{} filename_plots.root [-b]'.format(argv[0]))
    print('Example:')
    print('{} output_300n_plots.root -b'.format(argv[0]))
    return

##########################################
# https://www.tutorialspoint.com/python/python_command_line_arguments.htm
def main(argv):
    #if len(sys.argv) > 1:
    #  foo = sys.argv[1]

    pngdir = 'png_results/'
    pdfdir = 'pdf_results/'
    os.system(f'mkdir {pngdir}')
    os.system(f'mkdir {pdfdir}')

    opt2d = 'colz'
    
    ### https://www.tutorialspoint.com/python/python_command_line_arguments.htm
    ### https://pymotw.com/2/getopt/
    ### https://docs.python.org/3.1/library/getopt.html
    #gBatch = True
    gBatch = False
    gTag=''
    print(argv[1:])
    try:
        # options that require an argument should be followed by a colon (:).
        opts, args = getopt.getopt(argv[2:], 'hbt:', ['help','batch','tag='])
        print('Got options:')
        print(opts)
        print(args)
    except getopt.GetoptError:
        print('Parsing...')
        print ('Command line argument error!')
        print('{:} [ -h -b --batch -tTag --tag="MyCoolTag"]]'.format(argv[0]))
        sys.exit(2)
    for opt,arg in opts:
        print('Processing command line option {} {}'.format(opt,arg))
        if opt == '-h':
            print('{:} [ -h -b --batch -tTag --tag="MyCoolTag"]'.format(argv[0]))
            sys.exit()
        elif opt in ("-b", "--batch"):
            gBatch = True
            print('OK, running in batch mode')
        elif opt in ("-t", "--tag"):
            gTag = arg
            print('OK, using user-defined histograms tag for output pngs {:}'.format(gTag,) )

    if gBatch:
        ROOT.gROOT.SetBatch(1)

    if len(argv) < 2:
        PrintUsage(argv)
        return

    ROOT.gStyle.SetOptFit(111)
    print('*** Settings:')
    print('tag={:}, batch={:}'.format(gTag, gBatch))


    ROOT.gStyle.SetPalette(ROOT.kSolar)
    
    
    #filename = 'output_300n_plots.root'
    filename = argv[1]
    rfile = ROOT.TFile(filename, 'read')
    nChannels = 19 # 32
    Hs = []
    Txts = []
  

    ftag = filename.split('/')[-1].replace('output_','').replace('_plots.root','')
    hbasenames = {
        'hRef_Time' : ROOT.kGreen,
        'hRef_Charge' : ROOT.kCyan,
        'hRef_Voltage' : ROOT.kMagenta,
        'hRef_nPeaks' : ROOT.kYellow,
        'hRef_Pedestal': ROOT.kBlue,
        'hRef_PedestalNbPeaks': ROOT.kGray,
    }
    
    os.system('mkdir -p pdf png')
    
    for hbasename in hbasenames:

        hs = []
        txts = []
           
        for ich in range(0, nChannels):
            # hack just for old tofs
            #if not ( ich >= 8 and ich <= 15):
            #    continue
            hname = hbasename + str(ich)
            h = rfile.Get(hname)
            try:
                print('ok, got ', h.GetName())
            except:
                print('ERROR getting histo {}!'.format(hname))
                continue

            print('Pushing ', ich, hname)
            hs.append(h)
        Hs.append(hs)

        canname = 'WCTEJuly2023_Quick1D_{}_{}'.format(ftag, hbasename)
        canname = canname.replace('_list_root','').replace('_ntuple','')
        #can = ROOT.TCanvas(canname, canname, 0, 0, 1600, 800)
        #cans.append(can)
        #can.Divide(8,4)
        for h in hs:
            try:
                print('ok, got ', h.GetName())
            except:
                print('ERROR getting histo!')
                continue
            ich = hs.index(h)

            if ich % 8 == 0:
                idigi = ich / 8
                off = 60
                cw = 4*400 + 4*off
                ch = 2*400
                if idigi > 1:
                    cw = 2*400 + 2*off
                    ch = 400
                can = ROOT.TCanvas(canname + f'_digi{idigi}', canname + f'_digi{idigi}', 0, 0, cw, ch)
                if idigi < 2:
                    can.Divide(4,2)
                else:
                    can.Divide(3,1)
                cans.append(can)

            
            can.cd(ich % 8 + 1)
            h.SetStats(0)
            #if not 'Time' in h.GetName():
            if 'nPeaks' in h.GetName():
                ROOT.gPad.SetLogy(1)
            #h.GetYaxis().SetRangeUser(1.e-4, h.GetYaxis().GetXmax())
            h.SetFillColor(hbasenames[hbasename])
            h.SetFillStyle(1111)
            h.SetTitle(ChNames[hs.index(h)])

            gmeans = []
            gsigmas = []
            xmaxes = []
            
            if 'Time' in h.GetName() and ich >= 8 and ich <= 15:
                #print('*** fitting {}'.format(h.GetName()))
                hname = h.GetName()
                fname = 'fit{}'.format(ich)
                fit = ROOT.TF1(fname, '[0]*exp(-(x-[1])^2/(2*[2]^2))', 0., 520.)
                fit.SetParameters(h.GetMaximum()/6., 80., 5.)
                h.Fit(fname, 'q', '')
                mean = fit.GetParameter(1)
                sigma = fit.GetParameter(2)
                #print(f'1) {hname } mean={mean:1.3f} ns; sigma={sigma:1.3f} ns')
                sf = 2.
                h.Fit(fname, 'q', '', mean - sf*sigma, mean + sf*sigma)
                mean = fit.GetParameter(1)
                sigma = fit.GetParameter(2)
                print(f'{hname } mean={mean:1.3f} ns; sigma={sigma:1.3f} ns')
                h.SetMaximum(1.2*h.GetMaximum())
                h.Draw('hist')
                h.GetXaxis().SetRangeUser(50, 120)
                fit.Draw('same')
                chi2 = fit.GetChisquare()
                ndf = fit.GetNDF()
                maxb = h.GetMaximumBin()
                bw = h.GetBinWidth(maxb)
                ymax = h.GetBinContent(maxb)
                xmax = h.GetBinCenter(maxb)
                if ndf > 0:
                    print(f'  chi2/ndf={chi2/ndf:1.3f}, bw={bw} mean-ymax={mean-xmax:1.3f}')
                stuff.append(fit)
                gmeans.append(mean)
                gsigmas.append(sigma)
                xmaxes.append(xmax)
            else:
                h.Draw('hist')

            print(gmeans)
            print(gsigmas)
            print(xmaxes)

            #mean
            
            # todo: times subtractions 
            
            #txt= 'Ch {} {} p={} MeV/c'.format(hs.index(h)+1, basetag, ftag.replace('n','').replace('p',''))
            #if 'p' in ftag:
            #    txt = txt + ' (Pos)'
            #elif 'n' in ftag:
            #    txt = txt + ' (Neg)'
            #else:
            #    txt = txt + ' (undef)'
            #text = ROOT.TLatex(0.120, 0.93, txt)
            #text.SetNDC()
            #text.Draw()
            #txts.append(text)


    # 2023 tof channels time diff analysis / calibration
    htdiffnames = []
    base = 'hTimeDiffTOF'
    htofdiffs = {}
    tofmeans = {}
    for itof in range(0,2):
        htofdiffs[itof] = []
        tofmeans[itof] = []
        for itch in range(1,4):
            hname = base + str(itof) + str(itch)
            htdiffnames.append(hname)
            h = rfile.Get(hname)
            htofdiffs[itof].append(h)

            
    canname = 'TofDiffsWCTEJuly2023_Quick1D_{}_{}'.format(ftag, hbasename)
    canname = canname.replace('_list_root','')
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    can.Divide(3,2)
    cans.append(can)
    ic = 1

    for itof,hs in htofdiffs.items():
        ich = -1
        for h in hs:
            ich = ich + 1
            can.cd(ic)
            h.Draw('hist')
            #h.GetXaxis().SetRangeUser(-4,8.)
            fname = 'fit_tofs_{}'.format(ic)
            fit = ROOT.TF1(fname, '[0]*exp(-(x-[1])^2/(2*[2]^2))', h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax())
            fit.SetParameters(h.GetMaximum()/6., h.GetMean(), h.GetStdDev())
            h.Fit(fname, 'q', '', )
            fit.Draw('same')
            mean = fit.GetParameter(1)
            sigma = fit.GetParameter(2)
            print(f'tof fit {itof} {ich}: {hname } mean={mean:1.3f} ns; sigma={sigma:1.3f} ns')
            stuff.append(fit)
            ic = ic+1
            tofmeans[itof].append(mean)
    print(tofmeans)
       
   # if not gBatch:
   #     ROOT.gApplication.Run()
   # return


    ######## absolute TOF measurement ##########
    htTOFnames = []
    base = 'hTimeTOF'
    htofTOFs = {}
    htofTOFs[0] = []
    for itch in range(0,4):
        hname = base + str(itch)
        htTOFnames.append(hname)
        h = rfile.Get(hname)
        htofTOFs[0].append(h)
    
    canname = 'AbsoluteTof_{}'.format(ftag[10:])
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    can.Divide(2,2)
    cans.append(can)
    ic = 1

    for itof, hs in htofTOFs.items():
        ich = -1
        for h in hs:
            ich = ich + 1
            can.cd(ic)
            ROOT.gPad.SetLogy(1);
            print("ok")
            h.Draw('hist')
            
            #h.GetXaxis().SetRangeUser(-4,8.)
            fname = 'fit_tofs_{}'.format(ic)
            fit = ROOT.TF1(fname, '[0]*exp(-(x-[1])^2/(2*[2]^2))+ [3]*exp(-(x-[4])^2/(2*[5]^2))', h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax()) #
            fit.SetParameters(h.GetMaximum()/6., h.GetMean()-1, h.GetStdDev(), h.GetMaximum()/6., h.GetMean()+1, h.GetStdDev()) #
            #try to fiut the peaks one by one
            #g1 = ROOT.TF1("g1", "gaus", 0, 15);
            #g2 = ROOT.TF1("g2", "gaus", 12, 20);
            #g3 = ROOT.TF1("g3", "gaus", 25, 30);

            #h.Fit(g1, "R");
            #h.Fit(g2, "R+");
            #h.Fit(g3, "+", "", 0, 50);


            #fit = g1 + g2 + g3 
            h.Fit(fname, 'q', '', )
            fit.Draw('same')
            #g1.Draw('same')
            #g2.Draw('same')
            #g3.Draw('same')
            mean = fit.GetParameter(1)
            sigma = fit.GetParameter(2)
            mean2 = fit.GetParameter(4)
            sigma2 = fit.GetParameter(5)
            mean3 = fit.GetParameter(6)
            sigma3 = fit.GetParameter(7)
            print("ok")
            print(f'tof fit {itof} {ich}: {hname } mean={mean:1.3f} ns; sigma={sigma:1.3f} ns')
            stuff.append(fit)
            ic = ic+1
            tofmeans[itof].append(mean)

    
##################################s
#   plot 2d hist act vs lead     #
##################################

    interest = []

    # interest
    canname = 'ACT2_3vsLeadGlass_{}'.format(ftag[10:])
    hname = 'hRef_pbA_act23A'
    hact23vsPbA = rfile.Get(hname)
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.cd()
    integral_full = hact23vsPbA.Integral()
    hact23vsPbA.GetXaxis().SetRangeUser(0, 16.)
    hact23vsPbA.GetYaxis().SetRangeUser(0, 15.)
    x1, x2, y1, y2 = 0.2, 1.3, 1.5, 4.5
    bx1 = hact23vsPbA.GetXaxis().FindBin(x1)
    bx2 = hact23vsPbA.GetXaxis().FindBin(x2)
    by1 = hact23vsPbA.GetYaxis().FindBin(y1)
    by2 = hact23vsPbA.GetYaxis().FindBin(y2)
    integral_zoom = hact23vsPbA.Integral(bx1, bx2, by1, by2)
    print(f'integral: ful={integral_full}, zoom={integral_zoom}')
    hact23vsPbA.SetTitle('ACT2+3 vs Lead Glass {}'.format(ftag[10:]))
    hact23vsPbA.DrawCopy(opt2d)
    adjustStats(hact23vsPbA)
    interest.append(hact23vsPbA)
    
    if False:
        line = makeLine(x1, x2, y1, y1)
        lines.append(line)
        line = makeLine(x1, x2, y2, y2)
        lines.append(line)
        line = makeLine(x1, x1, y1, y2)
        lines.append(line)
        line = makeLine(x2, x2, y1, y2)
        lines.append(line)
        txt = ROOT.TLatex(0.14, 0.8, f'box: {integral_zoom/1000:1.2f}k evts, full: {integral_full/1000:1.2f}k evts')
        txt.SetTextSize(0.04)
        txt.SetNDC()
        txt.Draw()
        stuff.append(txt)


    canname = 'TOFvsACT3_{}'.format(ftag[10:])
    hname = 'hRef_TOFACT3A'
    h = rfile.Get(hname)
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.cd()
    h.SetTitle('TOF vs ACT3 {}'.format(ftag[10:]))
    #h.GetYaxis().SetRangeUser(0, 15.)
    #h.GetXaxis().SetRangeUser(13.5, 16.0)
    h.DrawCopy(opt2d)
    adjustStats(h)


    # interest
    canname = 'TOFvsACT23_{}'.format(ftag[10:])
    hname = 'hRef_TOFACT23A'
    hTOFvsACT23 = rfile.Get(hname)
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.cd()
    hTOFvsACT23.SetTitle('TOF vs ACT23 {}'.format(ftag[10:]))
    hTOFvsACT23.GetXaxis().SetRangeUser(10., 14.0)
    hTOFvsACT23.GetYaxis().SetRangeUser(0, 4)
    hTOFvsACT23.DrawCopy(opt2d)
    adjustStats(hTOFvsACT23)
    interest.append(hTOFvsACT23)

    canname = 'TOFvsPb_{}'.format(ftag[10:])
    hname = 'hRef_PbATOF'
    hPbATOF = rfile.Get(hname)
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.cd()
    hPbATOF.SetTitle('Lead glass vs TOF {}'.format(ftag[10:]))
    hPbATOF.GetXaxis().SetRangeUser(0., 2.)
    hPbATOF.GetYaxis().SetRangeUser(10., 16.0)
    hPbATOF.DrawCopy(opt2d)
    adjustStats(hPbATOF)

    # interest
    canname = 'PbvsTOF_{}'.format(ftag[10:])
    hname = 'hRef_TOFPbA'
    hTOFPbA = rfile.Get(hname)
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.cd()
    hTOFPbA.SetTitle('Lead glass vs TOF {}'.format(ftag[10:]))
    hTOFPbA.GetXaxis().SetRangeUser(10., 16.)
    hTOFPbA.GetYaxis().SetRangeUser(0., 2)
    hTOFPbA.DrawCopy(opt2d)
    adjustStats(hTOFPbA)
    interest.append(hTOFPbA)
    #
    # canname = 'PbvsACT1_{}'.format(ftag[10:])
    # hname = 'hRef_pbA_act1C'
    # h = rfile.Get(hname)
    # can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    # cans.append(can)
    # can.cd()
    # # h.SetTitle('Lead glass vs ACT1 {}'.format(ftag[10:]))
    # # h.GetXaxis().SetRangeUser(0., 10.)
    # # h.GetYaxis().SetRangeUser(0., 16.0)
    # h.Draw(opt2d)
    # adjustStats(h)

    canname = 'TOFWindACT23_{}'.format(ftag[10:])
    hname = 'hRef_TOFWindACT23C'
    hTOFWindACT23 = rfile.Get(hname)
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.cd()
    hTOFWindACT23.SetTitle('TOF vs ACT23 WINDOW int. {}'.format(ftag[10:]))
    hTOFWindACT23.GetYaxis().SetRangeUser(0., 4.)
    hTOFWindACT23.GetXaxis().SetRangeUser(10., 14.0)
    hTOFWindACT23.Draw(opt2d)
    adjustStats(hTOFWindACT23)
    interest.append(hTOFWindACT23)

    canname = 'TOFACT0WindC_{}'.format(ftag[10:])
    hname = 'hRef_TOFACT0WindC'
    TOFACT0WindC = rfile.Get(hname)
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.cd()
    TOFACT0WindC.SetTitle('TOF vs ACT0 WINDOW int. {}'.format(ftag[10:]))
    TOFACT0WindC.GetYaxis().SetRangeUser(0., 1.)
    TOFACT0WindC.GetXaxis().SetRangeUser(10., 14.0)
    TOFACT0WindC.Draw(opt2d)
    # ROOT.gPad.SetLogy(3);
    adjustStats(TOFACT0WindC)
    interest.append(TOFACT0WindC)


    canname = 'TOFACT1WindC_{}'.format(ftag[10:])
    hname = 'hRef_TOFACT1WindC'
    TOFACT1WindC = rfile.Get(hname)
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.cd()
    TOFACT1WindC.SetTitle('TOF vs ACT1 WINDOW int. {}'.format(ftag[10:]))
    TOFACT1WindC.GetYaxis().SetRangeUser(0., 1.)
    TOFACT1WindC.GetXaxis().SetRangeUser(10., 14.0)
    TOFACT1WindC.Draw(opt2d)
    # ROOT.gPad.SetLogy(3);
    adjustStats(TOFACT1WindC)
    interest.append(TOFACT1WindC)


    canname = 'TOFACT0C_{}'.format(ftag[10:])
    hname = 'hRef_TOFACT0C'
    TOFACT0C = rfile.Get(hname)
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.cd()
    TOFACT0C.SetTitle('TOF vs ACT0 PEAK int. {}'.format(ftag[10:]))
    TOFACT0C.GetYaxis().SetRangeUser(0., 1.)
    TOFACT0C.GetXaxis().SetRangeUser(10., 14.0)
    TOFACT0C.Draw(opt2d)
    # ROOT.gPad.SetLogy(3);
    adjustStats(TOFACT0C)
    interest.append(TOFACT0C)

    canname = 'TOFACT1C_{}'.format(ftag[10:])
    hname = 'hRef_TOFACT1C'
    TOFACT1C = rfile.Get(hname)
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.cd()
    TOFACT1C.SetTitle('TOF vs ACT1 PEAK int. {}'.format(ftag[10:]))
    TOFACT1C.GetYaxis().SetRangeUser(0., 1.)
    TOFACT1C.GetXaxis().SetRangeUser(10., 14.0)
    TOFACT1C.Draw(opt2d)
    # ROOT.gPad.SetLogy(3);
    adjustStats(TOFACT1C)
    interest.append(TOFACT1C)





    canname = 'TOFall_{}'.format(ftag[10:])
    hname = 'hTOFAll'
    h = rfile.Get(hname)
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.cd()
    h.SetTitle('TOF(all) {}'.format(ftag[10:]))
    h.GetXaxis().SetRangeUser(10., 50.)
    fit = ROOT.TF1(fname, '[0]*exp(-(x-[1])^2/(2*[2]^2)) + [3]*exp(-(x-[4])^2/(2*[5]^2))', h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax()) #
    fit.SetParameters(h.GetMaximum()/6., h.GetMean()-1, h.GetStdDev()-1, h.GetMaximum()/6., h.GetMean()+1, h.GetStdDev()) #
    h.Fit(fname, 'q', '', )
    h.Draw(opt2d)
    fit.Draw('same')
    ROOT.gPad.SetLogy(1);





    canname = 'CmpInterest_{}'.format(ftag[10:])
    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
    cans.append(can)
    can.Divide(2,2)
    ih = 1
    for h in interest:
        can.cd(ih)
        h.Draw('colz')
        adjustStats(h)
        ih = ih + 1
    
    
    #acraplet - investigate "weird electrons"
#
#    canname = 'hHC0CHC1C_weirdE{}'.format(ftag[10:])
#    hname = 'hweirdE_HC0AHC1A'
#    h = rfile.Get(hname)
#    can = ROOT.TCanvas(canname, canname, 0, 0, 1200, 800)
#    cans.append(can)
#    can.cd()
#    h.SetTitle('Hole counter amplitudes [weirdE] (act2a+act3a) / 2.) > 1.5 && 13.5 < tof < 16.5 {}'.format(ftag[10:]))
#    #h.GetXaxis().SetRangeUser(10., 50.)
#    h.Draw("hist")







    #h.colz()

##################################
#       plots all the canvas     #
##################################

    print(tofmeans)

    srun = ''
    tokens = filename.split('_')
    for token in tokens:
        if '00' in token:
            srun = token.replace('000','')
    pnote = makeMomentumLabel(srun)
    stuff.append(pnote)
    
    for can in cans:
        can.cd()
        if 'vs' in can.GetName():
            pnote.Draw()
        can.Update()
        can.Print(pngdir + can.GetName() + '.png')
        can.Print(pdfdir + can.GetName() + '.pdf')
    
    if not gBatch:
        ROOT.gApplication.Run()
    return



###################################
###################################
###################################

if __name__ == "__main__":
    # execute only if run as a script"
    main(sys.argv)
    
###################################
###################################
###################################

