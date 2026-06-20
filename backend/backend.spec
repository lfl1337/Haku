# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs

BACKEND_DIR = SPECPATH

datas = [
    (os.path.join(BACKEND_DIR, 'tools', 'texconv.exe'), 'tools'),
    (os.path.join(BACKEND_DIR, 'routers'), 'routers'),
    (os.path.join(BACKEND_DIR, 'services'), 'services'),
    (os.path.join(BACKEND_DIR, 'models'), 'models'),
]
binaries = []
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'multipart',
    'routers',
    'routers.process',
    'routers.search',
    'services',
    'services.background_remover',
    'services.image_processor',
    'services.dds_converter',
    'services.image_search',
    'models',
    'models.schemas',
]

for pkg in ('rembg', 'ddgs'):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# onnxruntime: only collect data files + native DLLs, not the full submodule tree
# (collect_all pulls in torch/transformers which are massive and break the build)
datas += collect_data_files('onnxruntime')
binaries += collect_dynamic_libs('onnxruntime')

a = Analysis(
    [os.path.join(BACKEND_DIR, 'main.py')],
    pathex=[BACKEND_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchvision', 'torchaudio',
        'transformers', 'tensorflow', 'keras',
        'matplotlib', 'pandas', 'sklearn', 'IPython',
        'notebook', 'jupyter', 'numba', 'llvmlite',
        'onnx',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
