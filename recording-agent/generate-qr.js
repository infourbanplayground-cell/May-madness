#!/usr/bin/env node
'use strict'

const fs = require('fs')
const path = require('path')
const QRCode = require('qrcode')

const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'))
const courts = Object.keys(config.cameras)

const outDir = path.join(__dirname, 'qr-codes')
fs.mkdirSync(outDir, { recursive: true })

;(async () => {
  for (const courtId of courts) {
    const url = `${config.apiBaseUrl}/record?court=${courtId}`
    const outFile = path.join(outDir, `${courtId}.png`)
    await QRCode.toFile(outFile, url, { width: 800, margin: 2 })
    console.log(`${courtId} -> ${url}\n  saved: ${outFile}`)
  }
})()
