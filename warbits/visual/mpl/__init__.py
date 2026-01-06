"""Matplotlib rendering utilities for the Visual Blueprint system.

This package intentionally contains *no simulation logic*.

It renders Visual Blueprints (wireframes) into a Matplotlib 3D axes using
high-performance `Line3DCollection` batching.

Design goals:
- Minimal allocations per frame.
- Few Matplotlib artists (batch, don't spam).
- Aesthetic: holographic / sim-replay wireframes (default neon-green).
"""
