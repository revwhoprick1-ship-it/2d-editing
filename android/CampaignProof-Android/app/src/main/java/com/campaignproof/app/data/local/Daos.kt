package com.campaignproof.app.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import kotlinx.coroutines.flow.Flow

@Dao
interface AccountDao {
    @Query("SELECT * FROM accounts ORDER BY connectedAtEpochMs DESC")
    fun observeAll(): Flow<List<AccountEntity>>

    @Query("SELECT * FROM accounts WHERE selectedForScan = 1")
    suspend fun getSelectedForScan(): List<AccountEntity>

    @Query("SELECT * FROM accounts WHERE id = :id")
    suspend fun getById(id: String): AccountEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(account: AccountEntity)

    @Query("UPDATE accounts SET selectedForScan = :selected WHERE id = :id")
    suspend fun setSelectedForScan(id: String, selected: Boolean)

    @Query("UPDATE accounts SET tokenStatus = :status, lastError = :error WHERE id = :id")
    suspend fun updateTokenStatus(id: String, status: TokenStatus, error: String?)

    @Query("DELETE FROM accounts WHERE id = :id")
    suspend fun deleteById(id: String)
}

@Dao
interface CampaignDao {
    @Query("SELECT * FROM campaigns ORDER BY isActive DESC, updatedAtEpochMs DESC")
    fun observeAll(): Flow<List<CampaignEntity>>

    @Query("SELECT * FROM campaigns WHERE isActive = 1 LIMIT 1")
    suspend fun getActive(): CampaignEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(campaign: CampaignEntity)

    @Query("UPDATE campaigns SET isActive = 0")
    suspend fun deactivateAll()

    @Query("UPDATE campaigns SET isActive = 1 WHERE id = :id")
    suspend fun setActiveById(id: String)

    @Transaction
    suspend fun activateCampaign(id: String) {
        deactivateAll()
        setActiveById(id)
    }

    @Query("DELETE FROM campaigns WHERE id = :id")
    suspend fun deleteById(id: String)
}

@Dao
interface ScannedVideoDao {
    @Query("SELECT * FROM scanned_videos ORDER BY viewCount DESC")
    fun observeAll(): Flow<List<ScannedVideoEntity>>

    @Query("SELECT * FROM scanned_videos WHERE accountId = :accountId")
    suspend fun getByAccount(accountId: String): List<ScannedVideoEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(videos: List<ScannedVideoEntity>)

    @Query("DELETE FROM scanned_videos WHERE accountId = :accountId")
    suspend fun deleteByAccount(accountId: String)
}

@Dao
interface RecordingDao {
    @Query("SELECT * FROM recordings ORDER BY recordedAtEpochMs DESC")
    fun observeAll(): Flow<List<RecordingEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(recording: RecordingEntity)

    @Query("UPDATE recordings SET status = :status WHERE id = :id")
    suspend fun updateStatus(id: String, status: RecordingStatus)

    @Query("DELETE FROM recordings WHERE id = :id")
    suspend fun deleteById(id: String)
}
