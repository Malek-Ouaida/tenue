import "framer-motion";

declare module "framer-motion" {
  interface MotionProps {
    initial?: unknown;
    animate?: unknown;
    transition?: unknown;
  }
}

declare module "lucide-react" {
  import * as React from "react";

  export type LucideProps = React.SVGProps<SVGSVGElement> & {
    color?: string;
    size?: string | number;
    strokeWidth?: string | number;
    absoluteStrokeWidth?: boolean;
  };

  export const Moon: React.FC<LucideProps>;
  export const Sun: React.FC<LucideProps>;
  export const Eye: React.FC<LucideProps>;
  export const EyeOff: React.FC<LucideProps>;
  export const Facebook: React.FC<LucideProps>;
}
