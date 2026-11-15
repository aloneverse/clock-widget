#!/usr/bin/env python3
"""Generates the full Clock Widget Android project. Run from repo root."""
import os

F = {}

F["settings.gradle.kts"] = r'''pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "ClockWidget"
include(":app")
'''

F["build.gradle.kts"] = r'''plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
}
'''

F["gradle.properties"] = r'''org.gradle.jvmargs=-Xmx2g -Dfile.encoding=UTF-8
android.nonTransitiveRClass=true
'''

F["app/build.gradle.kts"] = r'''plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.aloneverse.clockwidget"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.aloneverse.clockwidget"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}
'''

F["app/src/main/AndroidManifest.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission
        android:name="android.permission.SCHEDULE_EXACT_ALARM"
        android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.USE_EXACT_ALARM" />

    <queries>
        <package android:name="com.google.android.deskclock" />
        <package android:name="com.android.deskclock" />
        <package android:name="com.sec.android.app.clockpackage" />
        <package android:name="com.oneplus.deskclock" />
        <package android:name="com.coloros.alarmclock" />
        <package android:name="com.oplus.alarmclock" />
        <package android:name="com.android.BBKClock" />
        <intent>
            <action android:name="android.intent.action.SHOW_ALARMS" />
        </intent>
    </queries>

    <application
        android:allowBackup="true"
        android:label="@string/app_name"
        android:theme="@android:style/Theme.DeviceDefault.Light">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <receiver
            android:name=".ClockWidget"
            android:exported="true">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
                <action android:name="android.intent.action.BOOT_COMPLETED" />
                <action android:name="android.intent.action.TIME_SET" />
                <action android:name="android.intent.action.TIMEZONE_CHANGED" />
                <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />
                <action android:name="android.intent.action.USER_PRESENT" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/clock_widget_info" />
        </receiver>
    </application>
</manifest>
'''

F["app/src/main/java/com/aloneverse/clockwidget/MainActivity.kt"] = r'''package com.aloneverse.clockwidget

import android.app.Activity
import android.os.Bundle
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val tv = TextView(this)
        tv.text = "Clock Widget installed ✅\n\nHome screen pe khali jagah long press karo → Widgets → \"Clock Widget\" select karo."
        tv.textSize = 18f
        tv.setPadding(48, 120, 48, 48)
        setContentView(tv)
    }
}
'''

F["app/src/main/java/com/aloneverse/clockwidget/ClockWidget.kt"] = r'''package com.aloneverse.clockwidget

import android.app.AlarmManager
import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.Typeface
import android.os.Build
import android.provider.AlarmClock
import android.text.format.DateFormat
import android.widget.RemoteViews
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class ClockWidget : AppWidgetProvider() {

    override fun onUpdate(context: Context, manager: AppWidgetManager, ids: IntArray) {
        update(context)
        schedule(context)
    }

    override fun onEnabled(context: Context) {
        schedule(context)
    }

    override fun onDisabled(context: Context) {
        cancel(context)
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        when (intent.action) {
            ACTION_TICK,
            Intent.ACTION_BOOT_COMPLETED,
            Intent.ACTION_TIME_CHANGED,
            Intent.ACTION_TIMEZONE_CHANGED,
            Intent.ACTION_MY_PACKAGE_REPLACED,
            Intent.ACTION_USER_PRESENT -> {
                update(context)
                schedule(context)
            }
        }
    }

    companion object {
        const val ACTION_TICK = "com.aloneverse.clockwidget.TICK"

        private val CLOCK_PACKAGES = listOf(
            "com.google.android.deskclock",
            "com.android.deskclock",
            "com.sec.android.app.clockpackage",
            "com.oneplus.deskclock",
            "com.coloros.alarmclock",
            "com.oplus.alarmclock",
            "com.android.BBKClock"
        )

        private fun tickIntent(ctx: Context): PendingIntent {
            val i = Intent(ctx, ClockWidget::class.java).setAction(ACTION_TICK)
            return PendingIntent.getBroadcast(
                ctx, 1, i, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
        }

        fun schedule(ctx: Context) {
            val am = ctx.getSystemService(Context.ALARM_SERVICE) as AlarmManager
            val next = (System.currentTimeMillis() / 60000L) * 60000L + 60000L
            val pi = tickIntent(ctx)
            val canExact = Build.VERSION.SDK_INT < 31 || am.canScheduleExactAlarms()
            if (canExact) {
                am.setExactAndAllowWhileIdle(AlarmManager.RTC, next, pi)
            } else {
                am.setAndAllowWhileIdle(AlarmManager.RTC, next, pi)
            }
        }

        fun cancel(ctx: Context) {
            val am = ctx.getSystemService(Context.ALARM_SERVICE) as AlarmManager
            am.cancel(tickIntent(ctx))
        }

        private fun clockPendingIntent(ctx: Context): PendingIntent {
            var launch: Intent? = null
            for (p in CLOCK_PACKAGES) {
                val i = ctx.packageManager.getLaunchIntentForPackage(p)
                if (i != null) { launch = i; break }
            }
            val intent = (launch ?: Intent(AlarmClock.ACTION_SHOW_ALARMS))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            return PendingIntent.getActivity(
                ctx, 0, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
        }

        fun update(ctx: Context) {
            val mgr = AppWidgetManager.getInstance(ctx)
            val ids = mgr.getAppWidgetIds(ComponentName(ctx, ClockWidget::class.java))
            if (ids.isEmpty()) return

            val prefs = ctx.getSharedPreferences("clock_widget", Context.MODE_PRIVATE)
            val now = Date()
            val is24 = DateFormat.is24HourFormat(ctx)
            val time = SimpleDateFormat(if (is24) "H:mm" else "h:mm", Locale.getDefault()).format(now)
            val date = SimpleDateFormat("EEE, d MMM", Locale.getDefault()).format(now)

            val lastTime = prefs.getString("time", null)
            val lastDate = prefs.getString("date", null)
            var cur = prefs.getInt("cur", 0)
            val imgIds = intArrayOf(R.id.img0, R.id.img1)

            val views = RemoteViews(ctx.packageName, R.layout.widget_clock)

            if (lastTime == null || lastDate == null || (lastTime == time && lastDate == date)) {
                // nothing changed: just (re)draw the current frame, no animation
                views.setImageViewBitmap(imgIds[cur], render(ctx, date, time))
                views.setDisplayedChild(R.id.flipper, cur)
            } else {
                // time changed: old frame fades out, new frame emerges
                val next = 1 - cur
                views.setImageViewBitmap(imgIds[cur], render(ctx, lastDate, lastTime))
                views.setImageViewBitmap(imgIds[next], render(ctx, date, time))
                views.setDisplayedChild(R.id.flipper, next)
                cur = next
            }

            views.setOnClickPendingIntent(R.id.root, clockPendingIntent(ctx))

            prefs.edit()
                .putString("time", time)
                .putString("date", date)
                .putInt("cur", cur)
                .apply()

            mgr.updateAppWidget(ids, views)
        }

        private fun render(ctx: Context, date: String, time: String): Bitmap {
            val tf = try {
                Typeface.createFromAsset(ctx.assets, "Monoton-Regular.ttf")
            } catch (e: Exception) {
                Typeface.DEFAULT_BOLD
            }
            val textColor = Color.parseColor("#E8F1FF")
            val width = 800
            val maxW = 740f

            // fixed text size from a reference string so size never jumps between minutes
            val timePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                typeface = tf
                color = textColor
                textSize = 400f
            }
            val ref = "88:88"
            val rb = Rect()
            timePaint.getTextBounds(ref, 0, ref.length, rb)
            if (rb.width() > maxW) {
                timePaint.textSize = 400f * maxW / rb.width()
                timePaint.getTextBounds(ref, 0, ref.length, rb)
            }
            val tb = Rect()
            timePaint.getTextBounds(time, 0, time.length, tb)

            val datePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                typeface = Typeface.create("sans-serif-medium", Typeface.NORMAL)
                color = textColor
                textSize = 64f
                textAlign = Paint.Align.CENTER
            }
            val db = Rect()
            datePaint.getTextBounds(date, 0, date.length, db)

            val pad = 20
            val gap = 36
            val height = pad + db.height() + gap + rb.height() + pad

            val bmp = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
            val c = Canvas(bmp)

            c.drawText(date, width / 2f, (pad - db.top).toFloat(), datePaint)

            val timeTop = pad + db.height() + gap
            val x = (width - tb.width()) / 2f - tb.left
            val y = (timeTop - rb.top).toFloat()
            c.drawText(time, x, y, timePaint)
            return bmp
        }
    }
}
'''

F["app/src/main/res/layout/widget_clock.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@android:color/transparent">

    <ViewFlipper
        android:id="@+id/flipper"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:inAnimation="@anim/widget_in"
        android:outAnimation="@anim/widget_out"
        android:animateFirstView="false">

        <ImageView
            android:id="@+id/img0"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:scaleType="fitCenter" />

        <ImageView
            android:id="@+id/img1"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:scaleType="fitCenter" />
    </ViewFlipper>
</FrameLayout>
'''

F["app/src/main/res/anim/widget_in.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<set xmlns:android="http://schemas.android.com/apk/res/android"
    android:interpolator="@android:anim/decelerate_interpolator">
    <alpha
        android:fromAlpha="0.0"
        android:toAlpha="1.0"
        android:duration="750" />
    <translate
        android:fromYDelta="15%"
        android:toYDelta="0%"
        android:duration="750" />
    <scale
        android:fromXScale="0.92"
        android:toXScale="1.0"
        android:fromYScale="0.92"
        android:toYScale="1.0"
        android:pivotX="50%"
        android:pivotY="50%"
        android:duration="750" />
</set>
'''

F["app/src/main/res/anim/widget_out.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<set xmlns:android="http://schemas.android.com/apk/res/android"
    android:interpolator="@android:anim/accelerate_interpolator">
    <alpha
        android:fromAlpha="1.0"
        android:toAlpha="0.0"
        android:duration="450" />
    <translate
        android:fromYDelta="0%"
        android:toYDelta="-15%"
        android:duration="450" />
</set>
'''

F["app/src/main/res/xml/clock_widget_info.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:description="@string/widget_desc"
    android:initialLayout="@layout/widget_clock"
    android:minWidth="250dp"
    android:minHeight="110dp"
    android:targetCellWidth="4"
    android:targetCellHeight="2"
    android:resizeMode="horizontal|vertical"
    android:updatePeriodMillis="0"
    android:widgetCategory="home_screen" />
'''

F["app/src/main/res/values/strings.xml"] = r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Clock Widget</string>
    <string name="widget_desc">Transparent clock with smooth time animation</string>
</resources>
'''

for path, content in F.items():
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print("wrote", path)
