import React from 'react';

interface OffshoreLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const OffshoreLogo: React.FC<OffshoreLogoProps> = ({
  className = '',
  size = 'md',
}) => {
  const iconSize = size === 'sm' ? 28 : size === 'lg' ? 44 : 34;

  return (
    <div className={`flex items-center gap-3.5 select-none ${className}`}>
      {/* Exact Mountain Logo Icon from Source Image */}
      <div
        className="relative flex items-center justify-center shrink-0 rounded-sm overflow-hidden"
        style={{ width: iconSize, height: iconSize * 0.95 }}
      >
        <svg
          viewBox="0 0 100 90"
          className="w-full h-full drop-shadow-sm"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Triangular background container with light cyan glacial tint */}
          <polygon
            points="50,4 96,86 4,86"
            fill="url(#logoGlacialGradient)"
          />

          {/* Faceted mountain peaks inside the triangle */}
          {/* Left shadow slope */}
          <polygon
            points="50,4 28,86 4,86"
            fill="#347094"
            opacity="0.8"
          />
          
          {/* Central ridge shadow */}
          <polygon
            points="50,4 46,86 28,86"
            fill="#235172"
            opacity="0.9"
          />

          {/* Right sunlit ridge */}
          <polygon
            points="50,4 72,86 96,86"
            fill="#e2f1f8"
            opacity="0.95"
          />

          {/* Secondary smaller peak inside */}
          <polygon
            points="68,36 86,86 52,86"
            fill="#ffffff"
          />
          <polygon
            points="68,36 52,86 64,86"
            fill="#6098be"
            opacity="0.85"
          />

          {/* Pure snowy apex on main peak */}
          <polygon
            points="50,4 42,34 50,30 58,34"
            fill="#ffffff"
          />
          <polygon
            points="50,4 58,34 50,30"
            fill="#ffffff"
          />

          <defs>
            <linearGradient id="logoGlacialGradient" x1="50" y1="4" x2="50" y2="86" gradientUnits="userSpaceOnUse">
              <stop stopColor="#9ecbdc" />
              <stop offset="1" stopColor="#5b9bb8" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {/* Brand Wordmark & Navigation Intelligence Subtitle */}
      <div className="flex flex-col tracking-wider">
        <span className="font-montserrat font-semibold text-white tracking-[0.16em] text-[15px] sm:text-[17px] leading-tight">
          OFFSHORE
        </span>
        <span className="font-montserrat font-medium text-white/90 tracking-[0.24em] text-[8px] sm:text-[9.5px] uppercase leading-none mt-0.5">
          NAVIGATION INTELLIGENCE
        </span>
      </div>
    </div>
  );
};
