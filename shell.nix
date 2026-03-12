# Nix shell configuration for MooAId
# Run `nix-shell` to enter the development environment

{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "mooaid";
  
  buildInputs = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.virtualenv
  ];

  shellHook = ''
    echo "MooAId Development Environment"
    echo "=============================="
    echo ""
    echo "To install dependencies:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -e '.[dev]'"
    echo ""
    echo "To run the API server:"
    echo "  mooaid serve"
    echo ""
    echo "To use the CLI:"
    echo "  mooaid --help"
  '';
}
