#!/usr/bin/env python
# -*- coding: utf-8 -*-

import magic
ms = magic.open(magic.NONE)
ms.load()

def filetype(fpath):
    tp = ms.file(fpath)
    return tp
