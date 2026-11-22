package com.campaignproof.app.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverter
import androidx.room.TypeConverters

class CampaignProofConverters {
    @TypeConverter fun fromPlatform(v: Platform): String = v.name
    @TypeConverter fun toPlatform(v: String): Platform = Platform.valueOf(v)

    @TypeConverter fun fromCampaignPlatform(v: CampaignPlatform): String = v.name
    @TypeConverter fun toCampaignPlatform(v: String): CampaignPlatform = CampaignPlatform.valueOf(v)

    @TypeConverter fun fromAuthMode(v: AuthMode): String = v.name
    @TypeConverter fun toAuthMode(v: String): AuthMode = AuthMode.valueOf(v)

    @TypeConverter fun fromTokenStatus(v: TokenStatus): String = v.name
    @TypeConverter fun toTokenStatus(v: String): TokenStatus = TokenStatus.valueOf(v)

    @TypeConverter fun fromEligibility(v: EligibilityStatus): String = v.name
    @TypeConverter fun toEligibility(v: String): EligibilityStatus = EligibilityStatus.valueOf(v)

    @TypeConverter fun fromRecordingStatus(v: RecordingStatus): String = v.name
    @TypeConverter fun toRecordingStatus(v: String): RecordingStatus = RecordingStatus.valueOf(v)
}

@Database(
    entities = [
        AccountEntity::class,
        CampaignEntity::class,
        ScannedVideoEntity::class,
        RecordingEntity::class
    ],
    version = 1,
    exportSchema = false
)
@TypeConverters(CampaignProofConverters::class)
abstract class CampaignProofDatabase : RoomDatabase() {
    abstract fun accountDao(): AccountDao
    abstract fun campaignDao(): CampaignDao
    abstract fun scannedVideoDao(): ScannedVideoDao
    abstract fun recordingDao(): RecordingDao

    companion object {
        @Volatile private var INSTANCE: CampaignProofDatabase? = null

        fun getInstance(context: Context): CampaignProofDatabase {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    CampaignProofDatabase::class.java,
                    "campaignproof.db"
                ).build().also { INSTANCE = it }
            }
        }
    }
}
