{ pkgs }:
pkgs.mkShell {
  packages = with pkgs; [
    # Node.js ecosystem
    nodejs_22
    pnpm
    
    # Python ecosystem
    python311
    python311Packages.pip
    
    # Browser automation
    chromium
    chromedriver
    
    # Terminal multiplexer
    zellij
    
    # Utilities
    jq
  ];

  shellHook = ''
    echo "🚀 loan-scout development environment loaded"
    echo "   - Node.js: $(node --version)"
    echo "   - pnpm: $(pnpm --version)"
    echo "   - Python: $(python --version)"
    echo ""
    echo "Run 'pnpm dev' to start the application"
  '';
}
