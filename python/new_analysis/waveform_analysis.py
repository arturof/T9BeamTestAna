import numpy as np


class WaveformAnalysis:
    """
    This class holds an array of waveforms, for quickly doing waveform analysis on all waveforms
    """
    peak_rise_time_fraction = 0.4  # signal time is when the waveform passes this fraction of the peak amplitude
    impedance = 50  # for calculating integrated charge

    def __init__(self, waveforms, threshold=0.01, analysis_window=(0, 200), pedestal_window=(200, 420),
                 reverse_polarity=True, ns_per_sample=2, voltage_scale=0.000610351, time_offset=0):

        self.waveforms = np.array(waveforms)
        self.threshold = threshold
        self.reverse_polarity = reverse_polarity
        self.ns_per_sample = ns_per_sample
        self.voltage_scale = voltage_scale
        self.analysis_window = analysis_window
        self.pedestal_window = pedestal_window
        self.analysis_bins = range(analysis_window[0]//ns_per_sample, analysis_window[1]//ns_per_sample)
        self.pedestal_bins = range(pedestal_window[0]//ns_per_sample, pedestal_window[1]//ns_per_sample)
        self.time_offset = time_offset
        self.peak_locations = None
        self.amplitudes = None

    def find_pedestals(self):
        """Finds the pedestal of each waveform by taking the mean in the pedestal window. Also finds the standard deviation"""
        self.amplitudes = self.waveforms * self.voltage_scale
        self.pedestals = np.mean(self.amplitudes[:, self.pedestal_bins], axis=1, keepdims=True)
        self.pedestal_sigmas = np.std(self.amplitudes[:, self.pedestal_bins], axis=1, keepdims=True)
        self.amplitudes -= self.pedestals
        if self.reverse_polarity:
            self.amplitudes *= -1

    def find_peaks(self):
        """Finds the peak voltage in the analysis window of each waveform"""
        if self.amplitudes is None:
            self.find_pedestals()
        self.peak_locations = np.argmax(self.amplitudes[:, self.analysis_bins], axis=1, keepdims=True)
        self.peak_times = self.analysis_window[0] + (self.peak_locations + 0.5) * self.ns_per_sample
        self.peak_voltages = np.take_along_axis(self.amplitudes[:, self.analysis_bins], self.peak_locations, axis=1).reshape(self.peak_locations.shape)

    def calculate_signal_times(self):
        """Finds the signal time of each waveform as the interpolated time before the peak where the voltage reaches 0.4*[peak voltage]"""
        if self.peak_locations is None:
            self.find_peaks()
        signal_times = []
        for peak, loc, amp in zip(self.peak_voltages[:, 0], self.peak_locations[:, 0], self.amplitudes):
            if loc == 0:
                signal_times.append([0])
            else:
                loc += self.analysis_bins[0]
                threshold = self.peak_rise_time_fraction*peak
                i = loc - np.argmax(amp[loc-1::-1] < threshold)  # location before peak where amplitude passes fraction*peak
                time_range = [self.analysis_window[0]+(i-1), self.analysis_window[0]+i]
                signal_times.append([np.interp(threshold, amp[i-1:i+1], time_range)])
        self.signal_times = np.array(signal_times)*self.ns_per_sample + self.time_offset

    def integrate_charges(self):
        """Calculates the integrated charge of each waveform's range around the peak that is more than 3x the standard deviation of the pedestal"""
        if self.peak_locations is None:
            self.find_peaks()
        below_threshold = self.amplitudes < (3*self.pedestal_sigmas)
        indices = np.arange(self.amplitudes.shape[1])
        peak_indices = self.peak_locations + self.analysis_bins[0]
        before_peak_fall = np.cumsum((indices > peak_indices) & below_threshold, axis=1) == 0
        after_peak_rise = np.cumsum(((indices < peak_indices) & below_threshold)[:, ::-1], axis=1)[:, ::-1] == 0
        self.integrated_charges = np.sum(self.amplitudes*(before_peak_fall & after_peak_rise), axis=1, keepdims=True)
        self.integrated_charges *= self.ns_per_sample / self.impedance

    def run_analysis(self):
        """Finds each waveform peak, calculates the time, integrates the charge, and checks if it is over threshold"""
        self.find_peaks()
        self.calculate_signal_times()
        self.integrate_charges()
        self.is_over_threshold = self.peak_voltages > self.threshold
