{ pkgs }:
pkgs.mkShell {
  packages = with pkgs; [
    # Node.js ecosystem
    nodejs_22
    pnpm

    # Formatting & linting
    dprint
    
    # Python ecosystem
    python311
    python311Packages.pip
    stdenv.cc.cc.lib
    
    # Browser automation
    chromium
    chromedriver
    
    # Terminal multiplexer
    zellij
    
    # Utilities
    jq
  ];

  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc ]}:$LD_LIBRARY_PATH
    echo "🚀 loan-scout development environment loaded"
    echo "   - Node.js: $(node --version)"
    echo "   - pnpm: $(pnpm --version)"
    echo "   - dprint: $(dprint --version)"
    echo "   - Python: $(python --version)"
    echo ""
    echo "Run 'pnpm dev' to start the application"
  '';
}
