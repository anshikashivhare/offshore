import React, { useState } from 'react';
import { X, ShieldAlert, Compass, MapPin, Anchor, Info, CheckCircle2, ChevronRight, Wind, Navigation } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  category: string;
  children: React.ReactNode;
}

export const IntelligenceModal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  category,
  children,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in">
      <div
        className="relative w-full max-w-2xl bg-[#0b1a2e]/95 border border-white/20 rounded-2xl shadow-2xl p-6 sm:p-8 text-white text-left overflow-hidden"
        style={{
          boxShadow: '0 25px 50px -12px rgba(4, 15, 30, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.1)',
        }}
      >
        {/* Background glow */}
        <div className="absolute top-0 right-0 w-72 h-72 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-6">
          <div>
            <span className="text-[11px] font-medium tracking-[0.25em] text-cyan-400 uppercase">
              {category}
            </span>
            <h2 className="text-xl sm:text-2xl font-montserrat font-medium text-white tracking-wide mt-1">
              {title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors text-white/80 hover:text-white cursor-pointer"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4 max-h-[65vh] overflow-y-auto pr-2 text-white/90 text-sm leading-relaxed">
          {children}
        </div>

        <div className="mt-8 pt-4 border-t border-white/10 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-full bg-white text-[#0b1a2e] font-semibold text-xs tracking-wider uppercase hover:bg-white/90 transition-colors cursor-pointer"
          >
            Return to Bridge
          </button>
        </div>
      </div>
    </div>
  );
};



export const NavTopicModal: React.FC<{
  activeKey: string | null;
  onClose: () => void;
}> = ({ activeKey, onClose }) => {
  if (!activeKey) return null;

  const contentMap: Record<
    string,
    { title: string; category: string; description: string; highlights: string[] }
  > = {
    missions: {
      title: 'Active Antarctic Missions',
      category: 'Polar Operations',
      description:
        'Continuous surveillance of 14 scientific expedition vessels, sub-Antarctic research supply convoys, and automated bathymetric gliders traversing Drake Passage and the Weddell Sea.',
      highlights: [
        'R/V Polarstern II - Station Arrival: Neumayer III (On Schedule)',
        'Sir David Attenborough - Rothera Station Transit: Clear Ice Corridor',
        'Autonomous Glider Wing Echo - Salinity & Thermocline Mapping',
      ],
    },
    route_planner: {
      title: 'Dynamic Routing Intelligence',
      category: 'Hydrographic Analysis',
      description:
        'OFFSHORE dynamically computes routes through multi-year sea-ice packs using sub-meter Sentinel Synthetic Aperture Radar (SAR), altimetry anomaly detection, and tidal glacier calving forecasts.',
      highlights: [
        'Automated collision avoidance with tabular icebergs A-23a & A-76',
        'Tidal surge compensation in narrow passages (Lemaire & Neumayer Channels)',
        '34% reduction in fuel consumption by harnessing Antarctic Circumpolar Current eddies',
      ],
    },
    risk: {
      title: 'Polar Risk Assessment Index',
      category: 'Maritime Safety',
      description:
        'Predictive machine-learning hazard matrices evaluating compressive ice pressure, katabatic wind shear from the Antarctic Ice Sheet, and sub-surface growler density.',
      highlights: [
        'Katabatic Wind Gale Alert: 48kt gusts forecast in Marguerite Bay',
        'Fast-Ice Fracture Index: Stable (Level 1 across primary corridors)',
        'POLARIS Risk Index Outcome: Standard voyage approval granted',
      ],
    },
    navigation: {
      title: 'Autonomous Polar Navigation',
      category: 'Guidance Systems',
      description:
        'Deep-latitude inertial navigation systems (INS) paired with multi-constellation GNSS (Galileo + GPS) and high-latitude compass deviation auto-correction for magnetic pole proximity.',
      highlights: [
        'High-Latitude Gyro Stabilization: 0.002° variance at 68° South',
        'LiDAR Ice Edge Detection: 360° situational awareness up to 5 nautical miles',
        'Forward-Looking Sonar (FLS): Active submerged ice keel profiling',
      ],
    },
    about: {
      title: 'About OFFSHORE Navigation Intelligence',
      category: 'Platform Overview',
      description:
        'OFFSHORE delivers autonomous situational intelligence, ice risk forecasting, and optimal routing for high-latitude polar navigation in the Southern Ocean and Antarctic maritime zones.',
      highlights: [
        'Validated across 120,000+ nautical miles of Antarctic passages',
        'Compliant with IMO Polar Code Chapters 1–12 and SOLAS specifications',
        'Sub-meter satellite radar updates every 4 hours from polar orbiters',
      ],
    },
    home: {
      title: 'OFFSHORE Bridge System',
      category: 'Bridge Command',
      description:
        'Welcome to OFFSHORE Navigation Intelligence. Access missions, real-time SAR ice overlays, and dynamic route calculations directly from the polar command console.',
      highlights: [
        'Operating in Southern Ocean Polar Zone A',
        'Sensors & radar feeds fully synchronized',
        'Press Plan A Voyage to generate custom route',
      ],
    },
  };

  const item = contentMap[activeKey] || contentMap.about;

  return (
    <IntelligenceModal
      isOpen={!!activeKey}
      onClose={onClose}
      category={item.category}
      title={item.title}
    >
      <div className="space-y-4">
        <p className="text-white/85 text-sm">{item.description}</p>
        <div className="space-y-2 pt-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-cyan-300">
            System Status & Intel
          </h4>
          <ul className="space-y-2">
            {item.highlights.map((h, i) => (
              <li
                key={i}
                className="flex items-start gap-2.5 text-xs text-white/80 p-2.5 rounded-lg bg-white/5 border border-white/10"
              >
                <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <span>{h}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </IntelligenceModal>
  );
};
