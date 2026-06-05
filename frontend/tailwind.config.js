/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        OEMPartner: {
          blue: '#0033A0',      // Primary OEMPartner Blue
          red: '#E60012',       // OEMPartner Racing Red (accent)
          darkblue: '#002266',  // Darker blue for hover states
          lightblue: '#E8F1FF', // Light blue background
          gray: '#F5F7FA'       // Light gray background
        },
        mfg: {
          primary: '#0033A0',   // Manufacturing Group Manufacturing blue
          secondary: '#E60012', // Accent red
          dark: '#1a1a2e'       // Dark background
        }
      }
    }
  },
  plugins: []
};
